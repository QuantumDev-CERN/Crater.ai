"""Upload a PDF for a given revision; runs the full ingestion pipeline synchronously.

For a real pilot, move this to a background task/queue (Celery, arq, etc.) —
kept synchronous here so the MVP has the least moving parts to reason about
end-to-end.
"""
from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from backend.db.models import DocType, Revision
from backend.db.session import get_session
from backend.ingestion.pipeline import ingest_pdf

router = APIRouter(prefix="/ingest", tags=["ingestion"])

_UPLOAD_DIR = Path(tempfile.gettempdir()) / "crater_uploads"
_IMAGE_DIR = Path(tempfile.gettempdir()) / "crater_images"


@router.post("")
async def ingest_document(
    revision_id: str = Form(...),
    doc_type: DocType = Form(...),
    title: str = Form(...),
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
):
    revision = session.get(Revision, revision_id)
    if not revision:
        raise HTTPException(404, "Revision not found")

    _UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    dest = _UPLOAD_DIR / file.filename
    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    document = ingest_pdf(
        session=session,
        pdf_path=dest,
        revision_id=revision_id,
        product_id=revision.product_id,
        doc_type=doc_type,
        title=title,
        image_out_dir=_IMAGE_DIR / revision_id,
    )
    return {"document_id": document.id, "page_count": document.page_count}
