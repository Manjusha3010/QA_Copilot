from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional, Sequence

import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from copilot.config import Settings
from copilot.constants import ALL_COLLECTIONS, VECTOR_SIZE


def get_client(settings: Settings) -> QdrantClient:
    if settings.qdrant_url:
        return QdrantClient(url=settings.qdrant_url)
    return QdrantClient(path=settings.qdrant_path)


def ensure_collections(client: QdrantClient) -> None:
    existing = {c.name for c in client.get_collections().collections}
    for name in ALL_COLLECTIONS:
        if name in existing:
            continue
        client.create_collection(
            collection_name=name,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        )


def collection_exists(client: QdrantClient, name: str) -> bool:
    names = {c.name for c in client.get_collections().collections}
    return name in names


def upsert_chunks(
    client: QdrantClient,
    collection: str,
    vectors: np.ndarray,
    payloads: List[Dict[str, Any]],
    ids: Optional[Sequence[str]] = None,
) -> List[str]:
    if len(vectors) != len(payloads):
        raise ValueError("vectors and payloads length mismatch")
    point_ids = list(ids) if ids is not None else [str(uuid.uuid4()) for _ in payloads]
    points = [
        PointStruct(id=pid, vector=vec.tolist(), payload=pl)
        for pid, vec, pl in zip(point_ids, vectors, payloads)
    ]
    client.upsert(collection_name=collection, points=points)
    return point_ids


def search_collection(
    client: QdrantClient,
    collection: str,
    query_vector: Sequence[float],
    limit: int,
) -> List[dict]:
    hits = client.search(
        collection_name=collection,
        query_vector=list(query_vector),
        limit=limit,
        with_payload=True,
    )
    out = []
    for h in hits:
        payload = h.payload or {}
        out.append(
            {
                "id": str(h.id),
                "score": float(h.score) if h.score is not None else 0.0,
                "text": payload.get("text", ""),
                "payload": payload,
                "collection": collection,
            }
        )
    return out
