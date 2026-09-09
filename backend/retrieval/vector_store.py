"""
Qdrant wrapper. One collection for the whole system; every point carries
product_id / revision_id / doc_type / chunk_type as payload so queries
can be filtered to "this exact product+revision" — the metadata/revision
filtering plan.md §7 calls for.
"""
from __future__ import annotations

from qdrant_client import QdrantClient
from qdrant_client.http import models as qm

from backend.config import settings
from backend.retrieval.embeddings import get_embedding_provider


def get_client() -> QdrantClient:
    return QdrantClient(url=settings.qdrant_url)


def ensure_collection(client: QdrantClient | None = None) -> None:
    client = client or get_client()
    dim = get_embedding_provider().dim
    if not client.collection_exists(settings.qdrant_collection):
        client.create_collection(
            collection_name=settings.qdrant_collection,
            vectors_config=qm.VectorParams(size=dim, distance=qm.Distance.COSINE),
        )


def upsert_chunks(chunk_ids: list[str], texts: list[str], payloads: list[dict], client: QdrantClient | None = None) -> None:
    client = client or get_client()
    ensure_collection(client)
    vectors = get_embedding_provider().embed(texts)
    client.upsert(
        collection_name=settings.qdrant_collection,
        points=[
            qm.PointStruct(id=cid, vector=vec, payload=payload)
            for cid, vec, payload in zip(chunk_ids, vectors, payloads, strict=True)
        ],
    )


def semantic_search(
    query: str,
    top_k: int,
    product_id: str | None = None,
    revision_id: str | None = None,
    doc_type: str | None = None,
    client: QdrantClient | None = None,
) -> list[tuple[str, float]]:
    """Returns [(chunk_id, score), ...] ordered best-first."""
    client = client or get_client()
    query_vector = get_embedding_provider().embed([query])[0]

    must: list[qm.FieldCondition] = []
    if product_id:
        must.append(qm.FieldCondition(key="product_id", match=qm.MatchValue(value=product_id)))
    if revision_id:
        must.append(qm.FieldCondition(key="revision_id", match=qm.MatchValue(value=revision_id)))
    if doc_type:
        must.append(qm.FieldCondition(key="doc_type", match=qm.MatchValue(value=doc_type)))

    results = client.query_points(
        collection_name=settings.qdrant_collection,
        query=query_vector,
        query_filter=qm.Filter(must=must) if must else None,
        limit=top_k,
    ).points

    return [(str(point.id), point.score) for point in results]
