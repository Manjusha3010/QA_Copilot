from __future__ import annotations

import threading
from typing import TYPE_CHECKING, Any, List

import numpy as np

if TYPE_CHECKING:
    pass

_lock = threading.Lock()
_embedder: Any = None
_reranker: Any = None


def get_embedder(model_name: str):
    global _embedder
    with _lock:
        if _embedder is None:
            from FlagEmbedding import BGEM3FlagModel

            _embedder = BGEM3FlagModel(model_name, use_fp16=False)
        return _embedder


def get_reranker(model_name: str):
    global _reranker
    with _lock:
        if _reranker is None:
            from FlagEmbedding import FlagReranker

            _reranker = FlagReranker(model_name, use_fp16=False)
        return _reranker


def encode_dense(embedder, texts: List[str]) -> np.ndarray:
    out = embedder.encode(
        texts,
        return_dense=True,
        return_sparse=False,
        return_colbert_vecs=False,
    )
    return np.asarray(out["dense_vecs"], dtype=np.float32)


def rerank_pairs(reranker, query: str, passages: List[str]) -> List[float]:
    if not passages:
        return []
    pairs = [[query, p] for p in passages]
    scores = reranker.compute_score(pairs)
    if isinstance(scores, (int, float)):
        return [float(scores)]
    if hasattr(scores, "tolist"):
        return [float(x) for x in scores.tolist()]
    return [float(s) for s in scores]
