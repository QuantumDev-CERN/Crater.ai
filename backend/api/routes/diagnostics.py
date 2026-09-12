"""
The Phase 2 payoff endpoints: start a troubleshooting session on a symptom,
then keep feeding it observations/measurements until it concludes or
escalates.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session as DBSession

from backend.db.models import DiagnosticSession, Product, Revision
from backend.db.session import get_session
from backend.diagnostics.agent import run_turn, start_session
from backend.diagnostics.schema import DiagnosticSessionView, DiagnosticState

router = APIRouter(prefix="/diagnose", tags=["diagnostics"])


class StartDiagnosticRequest(BaseModel):
    product_id: str
    revision_id: str | None = None
    symptom: str


class RespondRequest(BaseModel):
    input: str
    input_kind: str = "observation"  # "symptom" | "observation" | "measurement"


def _to_view(session: DiagnosticSession) -> DiagnosticSessionView:
    return DiagnosticSessionView(
        session_id=session.id,
        product_id=session.product_id,
        revision_id=session.revision_id,
        status=session.status.value,
        state=DiagnosticState.model_validate(session.state),
    )


@router.post("/start", response_model=DiagnosticSessionView)
def start(payload: StartDiagnosticRequest, db: DBSession = Depends(get_session)):
    product = db.get(Product, payload.product_id)
    if not product:
        raise HTTPException(404, "Product not found")
    if payload.revision_id and not db.get(Revision, payload.revision_id):
        raise HTTPException(404, "Revision not found")

    session = start_session(db, payload.product_id, payload.revision_id, payload.symptom)
    return _to_view(session)


@router.post("/{session_id}/respond", response_model=DiagnosticSessionView)
def respond(session_id: str, payload: RespondRequest, db: DBSession = Depends(get_session)):
    session = db.get(DiagnosticSession, session_id)
    if not session:
        raise HTTPException(404, "Diagnostic session not found")
    if session.status.value != "active":
        raise HTTPException(400, f"Session already {session.status.value}; start a new session to continue troubleshooting.")

    run_turn(db, session, payload.input, input_kind=payload.input_kind)
    db.refresh(session)
    return _to_view(session)


@router.get("/{session_id}", response_model=DiagnosticSessionView)
def get_session_view(session_id: str, db: DBSession = Depends(get_session)):
    session = db.get(DiagnosticSession, session_id)
    if not session:
        raise HTTPException(404, "Diagnostic session not found")
    return _to_view(session)
