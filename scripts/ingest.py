#!/usr/bin/env python3
"""
Ingest the Vulcan OmniPro 220 PDF into the local knowledge stores.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from loguru import logger

from backend.config import settings
from backend.preprocessing.image_captioner import caption_images
from backend.preprocessing.pdf_extractor import extract
from backend.preprocessing.screenshot_renderer import render_page_screenshots
from backend.retrieval.table_store import ingest_tables
from backend.retrieval.vector_store import ingest_docs, ingest_image_captions


def _ensure_directories() -> None:
    settings.knowledge_dir.mkdir(parents=True, exist_ok=True)
    settings.images_dir.mkdir(parents=True, exist_ok=True)
    settings.screenshots_dir.mkdir(parents=True, exist_ok=True)


def _write_metadata(payload: dict) -> None:
    settings.metadata_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", required=True, type=Path)
    parser.add_argument("--skip-images", action="store_true")
    parser.add_argument("--skip-captions", action="store_true")
    parser.add_argument("--skip-screenshots", action="store_true")
    args = parser.parse_args()

    if not args.pdf.exists():
        logger.error(f"PDF not found: {args.pdf}")
        return 1

    _ensure_directories()
    t0 = time.perf_counter()

    docs, tables, image_entries = extract(args.pdf)
    ingest_docs(docs)
    ingest_tables(tables)

    screenshot_entries = []
    if not args.skip_screenshots:
        screenshot_entries = render_page_screenshots(args.pdf)

    caption_entries = []
    if not args.skip_images and not args.skip_captions:
        image_docs, caption_entries = caption_images(settings.images_dir, image_entries)
        ingest_image_captions(image_docs)

    _write_metadata(
        {
            "source_pdf": str(args.pdf),
            "generated_at_epoch": time.time(),
            "pages": screenshot_entries,
            "images": caption_entries,
            "image_entries": image_entries,
            "table_count": len(tables),
            "chunk_count": len(docs),
        }
    )

    elapsed = time.perf_counter() - t0
    logger.success(
        f"Done in {elapsed:.1f}s - {len(docs)} chunks, {len(tables)} tables, "
        f"{len(screenshot_entries)} screenshots, {len(caption_entries)} image captions"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
