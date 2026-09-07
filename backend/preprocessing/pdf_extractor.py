"""
PDF extraction for text and tables, with metadata normalized for retrieval.
"""
from __future__ import annotations

from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from loguru import logger
from unstructured.partition.pdf import partition_pdf

from backend.config import settings

TEXT_CATEGORIES = {"NarrativeText", "Title", "ListItem", "UncategorizedText"}


def extract(pdf_path: Path) -> tuple[list[Document], list[dict], list[dict]]:
    """
    Returns:
        docs: semantic-search chunks
        tables: structured raw tables for SQLite ingestion
        image_entries: extracted image metadata discovered during parsing
    """
    logger.info(f"Partitioning {pdf_path.name} ...")

    settings.images_dir.mkdir(parents=True, exist_ok=True)

    elements = partition_pdf(
        filename=str(pdf_path),
        strategy="hi_res",
        extract_images_in_pdf=True,
        extract_image_block_output_dir=str(settings.images_dir),
        infer_table_structure=True,
    )

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )

    docs: list[Document] = []
    tables: list[dict] = []
    image_entries: list[dict] = []

    for el in elements:
        page = getattr(el.metadata, "page_number", None)
        section = getattr(el.metadata, "section", None) or f"Page {page or 'Unknown'}"
        meta = {
            "page": page,
            "section": section,
            "source": pdf_path.name,
            "category": el.category,
        }

        if el.category == "Table":
            tables.append(
                {
                    "page": page,
                    "section": section,
                    "html": getattr(el.metadata, "text_as_html", "") or "",
                    "text": el.text or "",
                }
            )
            continue

        if el.category in TEXT_CATEGORIES and el.text:
            for chunk in splitter.create_documents([el.text], metadatas=[meta]):
                if len(chunk.page_content.strip()) >= settings.min_chunk_chars:
                    docs.append(chunk)
            continue

        image_path = getattr(el.metadata, "image_path", None)
        if image_path:
            image_entries.append(
                {
                    "page": page,
                    "section": section,
                    "image_path": image_path,
                    "category": el.category,
                }
            )

    logger.success(
        f"Extracted {len(docs)} chunks, {len(tables)} tables, {len(image_entries)} image entries"
    )
    return docs, tables, image_entries
