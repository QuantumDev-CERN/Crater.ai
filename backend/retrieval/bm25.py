"""
BM25 (keyword) retrieval over the same chunk corpus as the vector store.

MVP approach: rebuild a rank_bm25 index from the SQL rows matching the
requested product/revision/doc_type filters, on every query. That's
fine for a single-pilot-customer corpus (thousands of chunks); the
obvious next step once corpora grow is a persisted/incremental BM25
index (e.g. via a proper search engine) — noted here rather than
solved, per the "prove the loop first" MVP principle in plan.md §26.
"""
from __future__ import annotations

import re

from rank_bm25 import BM25Okapi
from sqlalchemy.orm import Session

from backend.db.models import Chunk, Document, Revision

_TOKEN_RE = re.compile(r"[A-Za-z0-9]+")


def _tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


def _candidate_chunks(
    session: Session,
    product_id: str | None,
    revision_id: str | None,
    doc_type: str | None,
) -> list[Chunk]:
    query = session.query(Chunk).join(Document, Chunk.document_id == Document.id).join(
        Revision, Document.revision_id == Revision.id
    )
    if revision_id:
        query = query.filter(Revision.id == revision_id)
    elif product_id:
        query = query.filter(Revision.product_id == product_id)
    if doc_type:
        query = query.filter(Document.doc_type == doc_type)
    return query.all()


def bm25_search(
    session: Session,
    query: str,
    top_k: int,
    product_id: str | None = None,
    revision_id: str | None = None,
    doc_type: str | None = None,
) -> list[tuple[str, float]]:
    """Returns [(chunk_id, score), ...] ordered best-first."""
    chunks = _candidate_chunks(session, product_id, revision_id, doc_type)
    if not chunks:
        return []

    corpus = [_tokenize(c.content) for c in chunks]
    bm25 = BM25Okapi(corpus)
    scores = bm25.get_scores(_tokenize(query))

    # Don't filter on score > 0: with small/homogeneous corpora (e.g. a single
    # ingested document) BM25's IDF term can go negative for every candidate,
    # which would zero out results entirely. Relative rank is what RRF fusion
    # actually consumes downstream, not the absolute score.
    ranked = sorted(zip(chunks, scores), key=lambda pair: pair[1], reverse=True)
    return [(c.id, float(score)) for c, score in ranked[:top_k]]
