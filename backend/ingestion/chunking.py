"""
Turn RawPage extraction output into persistable Chunk rows.

Table rows are serialized to markdown rather than kept as raw grids —
markdown tables embed and BM25-tokenize reasonably well and stay
human-readable in citations, at the cost of losing exact cell typing
(fine for retrieval; not fine if you later need to *compute* over
table values — flag that as a future need, not solved here).

Text chunking uses fixed-size character windows with overlap rather
than sentence/semantic splitting. It's the least surprising choice for
an MVP and avoids pulling in another NLP dependency; swap for a
semantic chunker once retrieval quality on real manuals is measured.
"""
from __future__ import annotations

from dataclasses import dataclass

from backend.config import settings
from backend.db.models import ChunkType
from backend.ingestion.ocr import caption_image, ocr_page_if_needed
from backend.ingestion.pdf_loader import RawPage


@dataclass
class PendingChunk:
    chunk_type: ChunkType
    page_number: int | None
    content: str
    extra: dict | None = None


def _split_text(text: str, size: int, overlap: int) -> list[str]:
    text = text.strip()
    if not text:
        return []
    if len(text) <= size:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks


def _table_to_markdown(table: list[list[str | None]]) -> str:
    rows = [[cell or "" for cell in row] for row in table]
    if not rows:
        return ""
    header, *body = rows
    md = ["| " + " | ".join(header) + " |", "| " + " | ".join(["---"] * len(header)) + " |"]
    md += ["| " + " | ".join(row) + " |" for row in body]
    return "\n".join(md)


def page_to_chunks(pdf_path: str, page: RawPage) -> list[PendingChunk]:
    chunks: list[PendingChunk] = []

    # 1. Text (with OCR fallback for scanned pages)
    text = ocr_page_if_needed(pdf_path, page.page_number, page.text)
    for piece in _split_text(text, settings.chunk_size_chars, settings.chunk_overlap_chars):
        chunks.append(PendingChunk(chunk_type=ChunkType.text, page_number=page.page_number, content=piece))

    # 2. Tables
    for table in page.tables:
        md = _table_to_markdown(table)
        if md:
            chunks.append(
                PendingChunk(
                    chunk_type=ChunkType.table,
                    page_number=page.page_number,
                    content=md,
                    extra={"rows": len(table), "cols": len(table[0]) if table else 0},
                )
            )

    # 3. Diagrams / embedded images
    for image_path in page.image_paths:
        caption = caption_image(image_path)
        content = caption if caption else f"[Diagram on page {page.page_number}, no OCR text detected]"
        chunks.append(
            PendingChunk(
                chunk_type=ChunkType.diagram,
                page_number=page.page_number,
                content=content,
                extra={"image_path": image_path},
            )
        )

    return chunks
