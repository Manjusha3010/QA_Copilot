from __future__ import annotations

from typing import Dict, List, Optional

from copilot.config import Settings
from copilot.constants import (
    ALL_COLLECTIONS,
    COLLECTION_PDFS,
    COLLECTION_PLAYWRIGHT,
    COLLECTION_SELENIUM,
    COLLECTION_VWO_TESTS,
)
from copilot import models_cache
from copilot import qdrant_ops


def _router_weights(query: str) -> Dict[str, float]:
    q = query.lower()
    w = {c: 1.0 for c in ALL_COLLECTIONS}

    boosts = [
        (
            COLLECTION_PLAYWRIGHT,
            ["playwright", " locator(", "page.goto", "expect(", "@playwright", "test.describe"],
            2.2,
        ),
        (
            COLLECTION_SELENIUM,
            ["selenium", "webdriver", "chromedriver", "webdriverwait", "by.", "expectedconditions"],
            2.2,
        ),
        (
            COLLECTION_VWO_TESTS,
            [
                "test case",
                "vwo",
                "scenario",
                "gherkin",
                "given ",
                "when ",
                "then ",
                "e2e",
                "regression",
            ],
            2.2,
        ),
        (
            COLLECTION_PDFS,
            [
                "pdf",
                "policy",
                "document",
                "jira",
                "summary",
                "release note",
                "spec",
                "markdown",
                "bug",
                "bug report",
                "notes",
            ],
            1.8,
        ),
    ]
    for col, keys, add in boosts:
        if any(k in q for k in keys):
            w[col] += add
    return w


def decide_collections(
    query: str,
    user_sources: Optional[List[str]],
) -> List[str]:
    """Router: keyword scores; ambiguous queries search all four collections."""
    if user_sources:
        return [s for s in user_sources if s in ALL_COLLECTIONS]
    w = _router_weights(query)
    ranked = sorted(ALL_COLLECTIONS, key=lambda c: w[c], reverse=True)
    top, second = w[ranked[0]], w[ranked[1]] if len(ranked) > 1 else 1.0
    if top < 2.5:
        return list(ALL_COLLECTIONS)
    if top - second < 0.35:
        return list(ALL_COLLECTIONS)
    if top >= 3.5 and top - second >= 1.0:
        return [ranked[0], ranked[1]]
    return ranked[: min(3, len(ranked))]


def _dedupe_hits(hits: List[dict]) -> List[dict]:
    seen = set()
    out = []
    for h in hits:
        key = (h["collection"], h["text"][:240])
        if key in seen:
            continue
        seen.add(key)
        out.append(h)
    return out


def retrieve_with_rerank(
    settings: Settings,
    client,
    embedder,
    reranker,
    query: str,
    user_sources: Optional[List[str]],
) -> List[dict]:
    collections = decide_collections(query, user_sources)
    qv = models_cache.encode_dense(embedder, [query])[0].tolist()
    per_k = settings.retrieve_k_per_collection
    pool: List[dict] = []
    for name in collections:
        pool.extend(qdrant_ops.search_collection(client, name, qv, per_k))
    pool = _dedupe_hits(pool)
    if not pool:
        return []
    passages = [h["text"][:4000] for h in pool]
    rscores = models_cache.rerank_pairs(reranker, query, passages)
    for h, s in zip(pool, rscores):
        h["rerank_score"] = s
    pool.sort(key=lambda x: x["rerank_score"], reverse=True)
    top = pool[: settings.context_chunks]
    citations = []
    for h in top:
        pl = h.get("payload") or {}
        citations.append(
            {
                "collection": h["collection"],
                "vector_score": h["score"],
                "rerank_score": h["rerank_score"],
                "text": h["text"],
                "path": pl.get("path"),
                "page": pl.get("page"),
                "source_type": pl.get("source_type"),
                "framework": pl.get("framework"),
                "title": pl.get("title"),
                "case_id": pl.get("case_id"),
                "doc_quality": pl.get("doc_quality"),
            }
        )
    return citations
