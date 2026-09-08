"""
The Phase-1 payoff endpoint: ask a question, get back evidence-grounded
chunks (not yet a diagnostic answer — that's Phase 2's Diagnostic Agent).

Response shape deliberately mirrors plan.md §8 (Evidence-Grounded
Answers): every result carries its source document, page, and
product/revision scope, so nothing here can be mistaken for an
unsourced claim.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.db.models import Document, DocType
from backend.db.session import get_session
from backend.retrieval.hybrid import hybrid_retrieve

router = APIRouter(prefix="/query", tags=["query"])


class QueryRequest(BaseModel):
    question: str
    product_id: str | None = None
    revision_id: str | None = None
    doc_type: DocType | None = None


@router.post("")
def query(payload: QueryRequest, session: Session = Depends(get_session)):
    results = hybrid_retrieve(
        session=session,
        query=payload.question,
        product_id=payload.product_id,
        revision_id=payload.revision_id,
        doc_type=payload.doc_type.value if payload.doc_type else None,
    )

    evidence = []
    for r in results:
        doc = session.get(Document, r.document_id)
        evidence.append(
            {
                "chunk_id": r.chunk_id,
                "chunk_type": r.chunk_type,
                "content": r.content,
                "page_number": r.page_number,
                "source_document": doc.title if doc else None,
                "doc_type": doc.doc_type.value if doc else None,
            }
        )

    return {"question": payload.question, "evidence": evidence}
