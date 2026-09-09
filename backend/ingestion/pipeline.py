"""
Top-level ingestion pipeline: PDF -> pages -> chunks -> (SQL + Qdrant) ->
optional knowledge extraction.

This is the single entry point both the CLI (scripts/ingest_docs.py) and
the API (/ingest route) call, so there's exactly one place that defines
"what ingesting a document means."
"""
from __future__ import annotations

from pathlib import Path

from sqlalchemy.orm import Session

from backend.db.models import Chunk, Component, ComponentRelationship, Document, DocType, Procedure
from backend.ingestion.chunking import page_to_chunks
from backend.ingestion.pdf_loader import load_pdf
from backend.knowledge.component_extraction import extract_from_chunk_text, persist_extraction
from backend.retrieval.vector_store import upsert_chunks


def ingest_pdf(
    session: Session,
    pdf_path: str | Path,
    revision_id: str,
    product_id: str,
    doc_type: DocType,
    title: str,
    image_out_dir: str | Path,
    run_knowledge_extraction: bool = True,
    existing_document_id: str | None = None,
) -> Document:
    pdf_path = Path(pdf_path)
    document = session.get(Document, existing_document_id) if existing_document_id else None

    if document:
        if document.revision_id != revision_id:
            raise ValueError("Existing document belongs to a different revision")
        all_chunks = session.query(Chunk).filter(Chunk.document_id == document.id).all()
    else:
        pages = load_pdf(pdf_path, image_out_dir)
        document = Document(
            revision_id=revision_id,
            doc_type=doc_type,
            title=title,
            source_path=str(pdf_path),
            page_count=len(pages),
        )
        session.add(document)
        session.flush()  # get document.id

        all_chunks: list[Chunk] = []
        for page in pages:
            for pending in page_to_chunks(str(pdf_path), page):
                row = Chunk(
                    document_id=document.id,
                    chunk_type=pending.chunk_type,
                    page_number=pending.page_number,
                    content=pending.content,
                    extra=pending.extra,
                )
                session.add(row)
                all_chunks.append(row)

        session.flush()  # get chunk ids
        session.commit()

    # Index into the vector store (BM25 reads straight from SQL, no separate step needed).
    if all_chunks:
        upsert_chunks(
            chunk_ids=[c.id for c in all_chunks],
            texts=[c.content for c in all_chunks],
            payloads=[
                {
                    "product_id": product_id,
                    "revision_id": revision_id,
                    "doc_type": doc_type.value,
                    "chunk_type": c.chunk_type.value,
                    "document_id": document.id,
                }
                for c in all_chunks
            ],
        )

    # Knowledge extraction (components/relationships/procedures), text chunks only —
    # tables/diagrams are noisier extraction targets and are deferred (see
    # component_extraction.py docstring).
    if run_knowledge_extraction:
        chunk_ids = [chunk.id for chunk in all_chunks]
        if existing_document_id and chunk_ids:
            # A retry starts with a clean extraction for this document. Vector
            # upserts are naturally idempotent because they reuse chunk IDs.
            session.query(ComponentRelationship).filter(ComponentRelationship.source_chunk_id.in_(chunk_ids)).delete(
                synchronize_session=False
            )
            session.query(Component).filter(Component.source_chunk_id.in_(chunk_ids)).delete(synchronize_session=False)
            session.query(Procedure).filter(Procedure.source_chunk_id.in_(chunk_ids)).delete(synchronize_session=False)

        try:
            for chunk in all_chunks:
                if chunk.chunk_type.value != "text" or len(chunk.content.strip()) < 100:
                    continue
                result = extract_from_chunk_text(chunk.content)
                if result.components or result.relationships or result.procedures:
                    persist_extraction(session, revision_id, chunk.id, result)
            session.commit()
        except Exception:
            session.rollback()
            raise

    return document
