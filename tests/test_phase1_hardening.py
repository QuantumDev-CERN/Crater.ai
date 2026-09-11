import pytest
from pydantic import ValidationError

from backend.api.routes.query import QueryRequest
from backend.retrieval import hybrid


def test_query_request_requires_revision_id():
    with pytest.raises(ValidationError):
        QueryRequest(question="What should I inspect?")


def test_hybrid_retrieval_uses_bm25_when_semantic_search_fails(monkeypatch):
    class Row:
        id = "chunk-1"
        content = "Terminal X12 should read 24 V."
        page_number = 7
        document_id = "document-1"

        class chunk_type:
            value = "text"

    class Query:
        def filter(self, *_args):
            return self

        def all(self):
            return [Row()]

    class Session:
        def query(self, *_args):
            return Query()

    def unavailable(*_args, **_kwargs):
        raise ConnectionError("Qdrant is unavailable")

    monkeypatch.setattr(hybrid, "semantic_search", unavailable)
    monkeypatch.setattr(hybrid, "bm25_search", lambda *_args, **_kwargs: [("chunk-1", 1.0)])
    monkeypatch.setattr(hybrid, "rerank", lambda _query, candidates, _top_k: [cid for cid, _ in candidates])

    results = hybrid.hybrid_retrieve(Session(), "What voltage is expected at X12?", revision_id="rev-1")

    assert [result.chunk_id for result in results] == ["chunk-1"]
