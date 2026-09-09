"""
OCR fallback + diagram captioning.

Two distinct jobs live here:
1. `ocr_page_if_needed` — some manuals are scanned images with no text
   layer at all; if native extraction returned near-nothing for a page,
   rasterize the page and OCR it so we don't silently lose content.
2. `caption_image` — for embedded images/schematics (which DO have
   surrounding page text, just not *inside* the image), run OCR on the
   image itself to pull labels/terminal numbers/callouts, which become
   the searchable text for that 'diagram' chunk (plan.md §5 Schematic
   Intelligence starts here — this is the cheap version; a
   vision-language captioning step is a natural upgrade slot).
"""
from __future__ import annotations

from pathlib import Path

import pymupdf as fitz
import pytesseract
from PIL import Image

from backend.config import settings

pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd

_MIN_CHARS_TO_SKIP_OCR = 40  # pages with less native text than this are treated as "scanned"


def needs_ocr(native_text: str) -> bool:
    return len(native_text.strip()) < _MIN_CHARS_TO_SKIP_OCR


def ocr_page_if_needed(pdf_path: str | Path, page_number: int, native_text: str) -> str:
    """Return native_text unchanged, or OCR'd text if the page looks scanned."""
    if not needs_ocr(native_text):
        return native_text

    with fitz.open(pdf_path) as doc:
        page = doc[page_number - 1]
        pix = page.get_pixmap(dpi=300)
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        return pytesseract.image_to_string(img)


def caption_image(image_path: str | Path) -> str:
    """OCR text embedded in a diagram/schematic image (labels, terminal numbers, callouts)."""
    try:
        return pytesseract.image_to_string(Image.open(image_path)).strip()
    except Exception:
        # A blurry/vector-only image with no OCR-able text is still a valid
        # diagram chunk — just with no caption text yet. Never fail ingestion
        # over one image.
        return ""
