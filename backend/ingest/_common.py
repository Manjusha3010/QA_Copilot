"""Upsert helpers for ingest scripts."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

import numpy as np

from backend.lib import embeddings, qdrant_store


def upsert_text_chunks(
    settings,
    client,
    embedder,
    collection: str,
    pairs: List[Tuple[str, Dict[str, Any]]],
    clear: bool,
    batch_size: int = 16,
) -> int:
    if not pairs:
        return 0
    if clear:
        qdrant_store.delete_collection_if_exists(client, collection)
        qdrant_store.ensure_collections(client)
    total = 0
    for i in range(0, len(pairs), batch_size):
        batch = pairs[i : i + batch_size]
        texts = [t for t, _ in batch]
        dense, sparse = embeddings.encode_batch(embedder, texts)
        payloads = [{"text": t, **m} for t, m in batch]
        qdrant_store.upsert_hybrid_batch(client, collection, dense, sparse, payloads)
        total += len(batch)
    return total
