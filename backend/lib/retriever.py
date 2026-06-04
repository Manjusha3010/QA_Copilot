"""Retrieve: optional rewrite → router → hybrid per collection → merge → rerank → top-k."""

from __future__ import annotations

from typing import Dict, List, Optional

from groq import Groq

from backend.lib import qdrant_store
from backend.lib.embeddings import encode_query
from backend.lib.prompts import ANSWER_SYSTEM, format_docs_for_prompt
from backend.lib.reranker import rerank_scores
from backend.lib.router import route_collections
from backend.lib.settings import Settings


def dedupe_hits(hits: List[dict]) -> List[dict]:
    seen = set()
    out = []
    for h in hits:
        key = (h["collection"], (h.get("text") or "")[:200])
        if key in seen:
            continue
        seen.add(key)
        out.append(h)
    return out


def retrieve_pipeline(
    settings: Settings,
    client,
    embedder,
    reranker,
    groq: Groq,
    question: str,
    history: Optional[List[dict]],
    source_override: Optional[List[str]],
) -> tuple[str, List[dict], List[str]]:
    from backend.lib import prompts as pr

    q = pr.rewrite_query(groq, settings, history or [], question) if history else question
    cols = route_collections(settings, groq, q, source_override)
    dq, sq = encode_query(embedder, q)
    pool: List[dict] = []
    for col in cols:
        pool.extend(
            qdrant_store.hybrid_search(
                client,
                col,
                dq,
                sq,
                settings.prefetch_limit,
                settings.top_k_per_collection,
            )
        )
    pool = dedupe_hits(pool)
    pool.sort(key=lambda x: x["score"], reverse=True)
    pool = pool[: settings.rerank_pool]
    texts = [(h.get("text") or "")[:8000] for h in pool]
    scores = rerank_scores(reranker, q, texts)
    for i, h in enumerate(pool):
        h["rerank_score"] = scores[i] if i < len(scores) else 0.0
    pool.sort(key=lambda x: x["rerank_score"], reverse=True)
    top = pool[: settings.rerank_top_k]
    return q, top, cols


def build_answer_non_stream(
    settings: Settings,
    groq: Groq,
    standalone_q: str,
    chunks: List[dict],
) -> str:
    ctx = format_docs_for_prompt(chunks)
    resp = groq.chat.completions.create(
        model=settings.groq_model,
        messages=[
            {"role": "system", "content": ANSWER_SYSTEM},
            {"role": "user", "content": f"Question:\n{standalone_q}\n\nContext:\n{ctx}"},
        ],
        temperature=0.2,
    )
    return (resp.choices[0].message.content or "").strip()


def citations_payload(chunks: List[dict]) -> List[dict]:
    out = []
    for i, h in enumerate(chunks, start=1):
        pl = h.get("payload") or {}
        out.append(
            {
                "id": i,
                "collection": h.get("collection"),
                "text": h.get("text", ""),
                "rerank_score": h.get("rerank_score", 0),
                "vector_score": h.get("score", 0),
                "vector_rrf_score": h.get("score", 0),
                "path": pl.get("path") or pl.get("source_path"),
                "page": pl.get("page"),
                "tc_id": pl.get("tc_id"),
                "jira_id": pl.get("jira_id"),
                "start_line": pl.get("start_line"),
                "end_line": pl.get("end_line"),
                "symbol": pl.get("symbol"),
            }
        )
    return out
