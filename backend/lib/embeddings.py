"""BGE-M3 dense + sparse (lexical) for Qdrant hybrid."""

from __future__ import annotations

import threading
from typing import Any, List, Tuple

import numpy as np
from qdrant_client.models import SparseVector

_lock = threading.Lock()
_model: Any = None


def get_embedder(model_name: str):
    global _model
    with _lock:
        if _model is None:
            from FlagEmbedding import BGEM3FlagModel

            _model = BGEM3FlagModel(model_name, use_fp16=False)
    return _model


def _lexical_to_sparse(lex: dict | None) -> SparseVector:
    if not lex:
        return SparseVector(indices=[0], values=[1e-5])
    items = []
    for k, v in lex.items():
        try:
            idx = int(k) if not isinstance(k, int) else k
        except (TypeError, ValueError):
            continue
        items.append((idx, float(v)))
    items.sort(key=lambda x: x[0])
    indices = [i for i, _ in items]
    values = [float(v) for _, v in items]
    if not indices:
        return SparseVector(indices=[0], values=[1e-5])
    return SparseVector(indices=indices, values=values)


def encode_batch(
    embedder, texts: List[str]
) -> Tuple[np.ndarray, List[SparseVector]]:
    out = embedder.encode(
        texts,
        batch_size=min(32, max(1, len(texts))),
        return_dense=True,
        return_sparse=True,
        return_colbert_vecs=False,
    )
    dense = np.asarray(out["dense_vecs"], dtype=np.float32)
    lex_list = out.get("lexical_weights")
    if lex_list is None:
        lex_list = [{} for _ in texts]
    elif isinstance(lex_list, dict):
        lex_list = [lex_list]
    while len(lex_list) < len(texts):
        lex_list.append({})
    sparse = [_lexical_to_sparse(d if isinstance(d, dict) else None) for d in lex_list[: len(texts)]]
    return dense, sparse


def encode_query(embedder, text: str) -> Tuple[List[float], SparseVector]:
    d, s = encode_batch(embedder, [text])
    return d[0].tolist(), s[0]
