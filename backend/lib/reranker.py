"""BGE cross-encoder reranker."""

from __future__ import annotations

import threading
from typing import Any, List

_lock = threading.Lock()
_reranker: Any = None


def get_reranker(model_name: str):
    global _reranker
    with _lock:
        if _reranker is None:
            from FlagEmbedding import FlagReranker

            _reranker = FlagReranker(model_name, use_fp16=False)
    return _reranker


def rerank_scores(reranker, query: str, passages: List[str]) -> List[float]:
    if not passages:
        return []
    pairs = [[query, p] for p in passages]
    scores = reranker.compute_score(pairs)
    if isinstance(scores, (int, float)):
        return [float(scores)]
    if hasattr(scores, "tolist"):
        return [float(x) for x in scores.tolist()]
    return [float(s) for s in scores]
