"""
Reranking step. Uses Claude as a lightweight cross-encoder substitute:
given the query and a shortlist of candidate chunk texts, ask it to
score relevance 0-100 and return sorted order. This piggybacks on the
"Claude Agent SDK" direction called out in plan.md §35 instead of
adding a separate cross-encoder model dependency, and doubles as the
seam where evidence-grounding checks (plan.md §8) can be added later.

Swap for a local cross-encoder (e.g. a sentence-transformers
CrossEncoder) if latency/cost on the rerank step becomes a problem —
the function signature is the contract to preserve.
"""
from __future__ import annotations

import json

from anthropic import Anthropic

from backend.config import settings

_RERANK_PROMPT = """You are scoring how relevant each passage is to a technician's question \
about a specific piece of industrial equipment. Score each passage 0-100 \
(100 = directly answers or is essential evidence; 0 = irrelevant).

Question: {query}

Passages:
{passages}

Respond with ONLY a JSON array of integers, one score per passage, in the same order. \
Example: [85, 10, 40]"""


def rerank(query: str, candidates: list[tuple[str, str]], top_k: int) -> list[str]:
    """
    candidates: [(chunk_id, chunk_text), ...]
    Returns chunk_ids, best-first, truncated to top_k.
    """
    if not candidates:
        return []
    if not settings.anthropic_api_key:
        # No API key configured (e.g. local dev without Claude access yet) —
        # fall back to the fusion order rather than hard-failing retrieval.
        return [cid for cid, _ in candidates[:top_k]]

    client = Anthropic(api_key=settings.anthropic_api_key)
    passages_block = "\n".join(f"[{i}] {text[:1000]}" for i, (_, text) in enumerate(candidates))

    response = client.messages.create(
        model=settings.anthropic_model,
        max_tokens=500,
        messages=[{"role": "user", "content": _RERANK_PROMPT.format(query=query, passages=passages_block)}],
    )
    raw = response.content[0].text.strip()

    try:
        scores = json.loads(raw)
    except (json.JSONDecodeError, IndexError):
        return [cid for cid, _ in candidates[:top_k]]

    scored = sorted(zip(candidates, scores), key=lambda pair: pair[1], reverse=True)
    return [cid for (cid, _), _score in scored[:top_k]]
