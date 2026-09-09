"""Durable, idempotent document ingestion endpoints for the Phase 1 MVP."""
from __future__ import annotations

import hashlib
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from backend.db.models import Document, DocType, IngestionJob, IngestionStatus, Revision
from backend.db.session import get_session
from backend.ingestion.pipeline import ingest_pdf

router = APIRouter(prefix="/ingest", tags=["ingestion"])

_UPLOAD_DIR = Path("data") / "uploads"
_IMAGE_DIR = Path("data") / "images"


def _job_response(job: IngestionJob, reused: bool = False) -> dict:
    return {
        "job_id": job.id,
        "document_id": job.document_id,
        "status": job.status.value,
        "stage": job.stage,
        "attempt_count": job.attempt_count,
        "error_message": job.error_message,
        "reused": reused,
    }


def _store_upload(file: UploadFile) -> tuple[Path, str]:
    if not file.filename or Path(file.filename).suffix.lower() != ".pdf":
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Only PDF uploads are supported")

    _UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    temporary = _UPLOAD_DIR / f"{uuid4()}.uploading"
    digest = hashlib.sha256()
    with temporary.open("wb") as output:
        while block := file.file.read(1024 * 1024):
            digest.update(block)
            output.write(block)

    content_sha256 = digest.hexdigest()
    content_path = _UPLOAD_DIR / f"{content_sha256}.pdf"
    if content_path.exists():
        temporary.unlink()
    else:
        temporary.replace(content_path)
    return content_path, content_sha256


def _run_job(session: Session, job: IngestionJob, revision: Revision) -> IngestionJob:
    try:
        job.stage = "ingesting"
        job.status = IngestionStatus.processing
        job.error_message = None
        session.commit()

        document = ingest_pdf(
            session=session,
            pdf_path=job.source_path,
            revision_id=revision.id,
            product_id=revision.product_id,
            doc_type=job.doc_type,
            title=job.title,
            image_out_dir=_IMAGE_DIR / revision.id,
            existing_document_id=job.document_id,
        )
        job.document_id = document.id
        job.status = IngestionStatus.completed
        job.stage = "completed"
        session.commit()
    except Exception as exc:
        session.rollback()
        job = session.get(IngestionJob, job.id)
        if not job:
            raise
        if not job.document_id:
            # Chunks are committed before external indexing. Remember that
            # partial document so a retry resumes it instead of duplicating it.
            partial_document = (
                session.query(Document)
                .filter(Document.revision_id == revision.id)
                .filter(Document.source_path == job.source_path)
                .order_by(Document.ingested_at.desc())
                .first()
            )
            if partial_document:
                job.document_id = partial_document.id
        job.status = IngestionStatus.failed
        job.stage = "failed"
        job.error_message = str(exc)[:2000]
        session.commit()
    return job


@router.post("", status_code=status.HTTP_201_CREATED)
async def ingest_document(
    revision_id: str = Form(...),
    doc_type: DocType = Form(...),
    title: str = Form(...),
    idempotency_key: str = Form(..., min_length=1, max_length=255),
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
):
    revision = session.get(Revision, revision_id)
    if not revision:
        raise HTTPException(404, "Revision not found")

    source_path, content_sha256 = _store_upload(file)
    existing = (
        session.query(IngestionJob)
        .filter(IngestionJob.revision_id == revision_id)
        .filter(IngestionJob.idempotency_key == idempotency_key)
        .first()
    )
    if existing:
        if existing.content_sha256 != content_sha256:
            raise HTTPException(409, "Idempotency key was already used for different content")
        return _job_response(existing, reused=True)

    duplicate_content = (
        session.query(IngestionJob)
        .filter(IngestionJob.revision_id == revision_id)
        .filter(IngestionJob.content_sha256 == content_sha256)
        .first()
    )
    if duplicate_content:
        return _job_response(duplicate_content, reused=True)

    job = IngestionJob(
        revision_id=revision_id,
        idempotency_key=idempotency_key,
        content_sha256=content_sha256,
        doc_type=doc_type,
        title=title,
        source_path=str(source_path),
        stage="queued",
    )
    session.add(job)
    session.commit()
    session.refresh(job)
    return _job_response(_run_job(session, job, revision))


@router.get("/jobs/{job_id}")
def get_ingestion_job(job_id: str, session: Session = Depends(get_session)):
    job = session.get(IngestionJob, job_id)
    if not job:
        raise HTTPException(404, "Ingestion job not found")
    return _job_response(job)


@router.post("/jobs/{job_id}/retry")
def retry_ingestion_job(job_id: str, session: Session = Depends(get_session)):
    job = session.get(IngestionJob, job_id)
    if not job:
        raise HTTPException(404, "Ingestion job not found")
    if job.status == IngestionStatus.completed:
        return _job_response(job, reused=True)
    if job.status == IngestionStatus.processing:
        raise HTTPException(409, "Ingestion job is already running")
    if not Path(job.source_path).is_file():
        raise HTTPException(409, "Original upload is unavailable; upload the document again with a new key")

    revision = session.get(Revision, job.revision_id)
    if not revision:
        raise HTTPException(404, "Revision not found")

    job.attempt_count += 1
    session.commit()
    return _job_response(_run_job(session, job, revision))
