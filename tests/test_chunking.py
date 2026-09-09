"""Smoke tests for chunking logic that don't need Qdrant/Anthropic/tesseract running."""
from backend.ingestion.chunking import _split_text, _table_to_markdown


def test_split_text_short_returns_single_chunk():
    assert _split_text("hello world", size=100, overlap=10) == ["hello world"]


def test_split_text_empty_returns_no_chunks():
    assert _split_text("   ", size=100, overlap=10) == []


def test_split_text_respects_overlap():
    text = "a" * 250
    chunks = _split_text(text, size=100, overlap=20)
    assert len(chunks) > 1
    # consecutive chunks should share `overlap` characters at the boundary
    assert chunks[0][-20:] == chunks[1][:20]


def test_table_to_markdown_basic():
    table = [["Terminal", "Voltage"], ["X12", "24V"], ["X14", "0V"]]
    md = _table_to_markdown(table)
    assert "| Terminal | Voltage |" in md
    assert "| X12 | 24V |" in md


def test_table_to_markdown_empty():
    assert _table_to_markdown([]) == ""
