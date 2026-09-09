"""
Embedding provider, kept behind a tiny interface so the local
sentence-transformers model can be swapped for a hosted embedding API
later without touching vector_store.py or hybrid.py.
"""
from __future__ import annotations

from functools import lru_cache

from backend.config import settings


class EmbeddingProvider:
    def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError

    @property
    def dim(self) -> int:
        raise NotImplementedError


class SentenceTransformerEmbeddings(EmbeddingProvider):
    def __init__(self, model_name: str | None = None):
        from sentence_transformers import SentenceTransformer  # lazy import: heavy dependency

        self.model_name = model_name or settings.embedding_model
        self._model = SentenceTransformer(self.model_name)

    def embed(self, texts: list[str]) -> list[list[float]]:
        return self._model.encode(texts, normalize_embeddings=True).tolist()

    @property
    def dim(self) -> int:
        return self._model.get_sentence_embedding_dimension()


@lru_cache(maxsize=1)
def get_embedding_provider() -> EmbeddingProvider:
    return SentenceTransformerEmbeddings()
