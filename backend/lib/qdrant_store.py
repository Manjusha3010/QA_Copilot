"""Qdrant: hybrid collections, upsert, RRF search."""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional, Sequence

import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    Fusion,
    FusionQuery,
    PointStruct,
    Prefetch,
    SparseVector,
    SparseVectorParams,
    VectorParams,
)

from backend.lib.collections import ALL_COLLECTIONS, DENSE_NAME, SPARSE_NAME, VECTOR_SIZE
from backend.lib.settings import Settings


def get_client(settings: Settings) -> QdrantClient:
    if settings.qdrant_url:
        return QdrantClient(url=settings.qdrant_url)
    return QdrantClient(path=settings.qdrant_path)


def collection_exists(client: QdrantClient, name: str) -> bool:
    return name in {c.name for c in client.get_collections().collections}


def ensure_collections(client: QdrantClient) -> None:
    existing = {c.name for c in client.get_collections().collections}
    for name in ALL_COLLECTIONS:
        if name in existing:
            continue
        client.create_collection(
            collection_name=name,
            vectors_config={DENSE_NAME: VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE)},
            sparse_vectors_config={SPARSE_NAME: SparseVectorParams()},
        )


def upsert_hybrid_batch(
    client: QdrantClient,
    collection: str,
    dense_rows: np.ndarray,
    sparse_rows: List[SparseVector],
    payloads: List[Dict[str, Any]],
    ids: Optional[Sequence[str]] = None,
) -> None:
    if len(dense_rows) != len(payloads) or len(sparse_rows) != len(payloads):
        raise ValueError("length mismatch")
    pids = list(ids) if ids else [str(uuid.uuid4()) for _ in payloads]
    points = []
    for pid, row, sp, pl in zip(pids, dense_rows, sparse_rows, payloads):
        points.append(
            PointStruct(
                id=pid,
                vector={
                    DENSE_NAME: row.tolist(),
                    SPARSE_NAME: sp,
                },
                payload=pl,
            )
        )
    client.upsert(collection_name=collection, points=points)


def hybrid_search(
    client: QdrantClient,
    collection: str,
    dense_query: Sequence[float],
    sparse_query: SparseVector,
    prefetch_limit: int,
    final_limit: int,
) -> List[dict]:
    try:
        hits = client.query_points(
            collection_name=collection,
            prefetch=[
                Prefetch(query=list(dense_query), using=DENSE_NAME, limit=prefetch_limit),
                Prefetch(query=sparse_query, using=SPARSE_NAME, limit=prefetch_limit),
            ],
            query=FusionQuery(fusion=Fusion.RRF),
            limit=final_limit,
            with_payload=True,
        ).points
    except Exception:
        hits = client.search(
            collection_name=collection,
            query_vector=list(dense_query),
            using=DENSE_NAME,
            limit=final_limit,
            with_payload=True,
        )
    out = []
    for h in hits:
        pl = h.payload or {}
        out.append(
            {
                "id": str(h.id),
                "score": float(h.score) if h.score is not None else 0.0,
                "text": pl.get("text", ""),
                "payload": pl,
                "collection": collection,
            }
        )
    return out


def delete_collection_if_exists(client: QdrantClient, name: str) -> None:
    if collection_exists(client, name):
        client.delete_collection(collection_name=name)
