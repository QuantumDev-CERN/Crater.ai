#!/usr/bin/env python
"""
CLI for Phase 1 ingestion — useful before any frontend exists.

Usage:
    python scripts/ingest_docs.py \\
        --manufacturer "Acme" --family "CNC-500" --model "CNC-500X" \\
        --revision "Rev C" \\
        --doc-type manual --title "CNC-500X Service Manual" \\
        path/to/manual.pdf

Creates the Product/Revision if they don't already exist (matched by
manufacturer+family+model / label), then runs the full ingestion
pipeline on the given PDF.
"""
from __future__ import annotations

from pathlib import Path

import typer

from backend.db.models import DocType, Product, Revision
from backend.db.session import SessionLocal, init_db
from backend.ingestion.pipeline import ingest_pdf

app = typer.Typer()


@app.command()
def main(
    pdf_path: Path,
    manufacturer: str = typer.Option(...),
    family: str = typer.Option(...),
    model: str = typer.Option(...),
    revision: str = typer.Option(..., help="Revision label, e.g. 'Rev C' or '2023'"),
    doc_type: DocType = typer.Option(DocType.manual),
    title: str = typer.Option(...),
):
    init_db()
    session = SessionLocal()

    product = (
        session.query(Product)
        .filter_by(manufacturer=manufacturer, family=family, model=model)
        .first()
    )
    if not product:
        product = Product(manufacturer=manufacturer, family=family, model=model)
        session.add(product)
        session.flush()
        typer.echo(f"Created product {product.id}")

    revision_row = session.query(Revision).filter_by(product_id=product.id, label=revision).first()
    if not revision_row:
        revision_row = Revision(product_id=product.id, label=revision)
        session.add(revision_row)
        session.flush()
        typer.echo(f"Created revision {revision_row.id}")

    session.commit()

    document = ingest_pdf(
        session=session,
        pdf_path=pdf_path,
        revision_id=revision_row.id,
        product_id=product.id,
        doc_type=doc_type,
        title=title,
        image_out_dir=Path("data/images") / revision_row.id,
    )
    typer.echo(f"Ingested document {document.id}: {document.page_count} pages")
    session.close()


if __name__ == "__main__":
    app()
