"""CRUD-ish endpoints for Product / Revision — the scaffolding you need before ingesting anything."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.db.models import Product, Revision
from backend.db.session import get_session

router = APIRouter(prefix="/products", tags=["products"])


class ProductCreate(BaseModel):
    manufacturer: str
    family: str
    model: str
    notes: str | None = None


class RevisionCreate(BaseModel):
    label: str
    notes: str | None = None


@router.post("")
def create_product(payload: ProductCreate, session: Session = Depends(get_session)):
    product = Product(**payload.model_dump())
    session.add(product)
    session.commit()
    session.refresh(product)
    return {"id": product.id, "manufacturer": product.manufacturer, "family": product.family, "model": product.model}


@router.get("")
def list_products(session: Session = Depends(get_session)):
    return [
        {"id": p.id, "manufacturer": p.manufacturer, "family": p.family, "model": p.model}
        for p in session.query(Product).all()
    ]


@router.post("/{product_id}/revisions")
def create_revision(product_id: str, payload: RevisionCreate, session: Session = Depends(get_session)):
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(404, "Product not found")
    revision = Revision(product_id=product_id, **payload.model_dump())
    session.add(revision)
    session.commit()
    session.refresh(revision)
    return {"id": revision.id, "product_id": product_id, "label": revision.label}


@router.get("/{product_id}/revisions")
def list_revisions(product_id: str, session: Session = Depends(get_session)):
    return [
        {"id": r.id, "label": r.label}
        for r in session.query(Revision).filter(Revision.product_id == product_id).all()
    ]
