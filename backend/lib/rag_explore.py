"""Full RAG trace for debugging / RAG Explorer UI."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from groq import Groq

from backend.lib import qdrant_store
from backend.lib.embeddings import encode_query
from backend.lib.prompts import ANSWER_SYSTEM, format_docs_for_prompt
from backend.lib.reranker import rerank_scores
from backend.lib.retriever import build_answer_non_stream, citations_payload, dedupe_hits
from backend.lib.router import route_collections_with_meta
from backend.lib.settings import Settings

_TEXT_PREVIEW = 800
_USER_PROMPT_MAX = 48_000


def _hit_summary(h: dict) -> dict:
    pl = h.get("payload") or {}
    text = h.get("text") or ""
    prev = text[:_TEXT_PREVIEW] + ("…" if len(text) > _TEXT_PREVIEW else "")
    return {
        "point_id": h.get("id"),
        "collection": h.get("collection"),
        "hybrid_rrf_score": h.get("score"),
        "text_preview": prev,
        "text_length": len(text),
        "path": pl.get("path") or pl.get("source_path"),
        "page": pl.get("page"),
        "tc_id": pl.get("tc_id"),
        "jira_id": pl.get("jira_id"),
        "start_line": pl.get("start_line"),
        "end_line": pl.get("end_line"),
        "symbol": pl.get("symbol"),
    }


def _pool_row(h: dict, rerank_score: Optional[float] = None) -> dict:
    row = _hit_summary(h)
    if rerank_score is not None:
        row["rerank_score"] = rerank_score
    return row


def run_rag_explore(
    settings: Settings,
    client,
    embedder,
    reranker,
    groq: Groq,
    question: str,
    history: Optional[List[dict]],
    source_override: Optional[List[str]],
) -> dict[str, Any]:
    from backend.lib import prompts as pr

    hist = history or []
    history_used = bool(hist)
    if history_used:
        rewritten = pr.rewrite_query(groq, settings, hist, question)
    else:
        rewritten = question

    cols, router_raw, router_fallback = route_collections_with_meta(
        settings, groq, rewritten, source_override
    )
    dq, sq = encode_query(embedder, rewritten)

    per_collection: Dict[str, List[dict]] = {}
    pool: List[dict] = []
    for col in cols:
        hits = qdrant_store.hybrid_search(
            client,
            col,
            dq,
            sq,
            settings.prefetch_limit,
            settings.top_k_per_collection,
        )
        per_collection[col] = [_hit_summary(h) for h in hits]
        pool.extend(hits)

    merged_count = len(pool)
    pool = dedupe_hits(pool)
    deduped_count = len(pool)
    pool.sort(key=lambda x: x["score"], reverse=True)
    pool = pool[: settings.rerank_pool]
    after_rrf_trim = [_pool_row(h) for h in pool]

    texts = [(h.get("text") or "")[:8000] for h in pool]
    rscores = rerank_scores(reranker, rewritten, texts)
    rerank_pairs = []
    for i, h in enumerate(pool):
        rs = rscores[i] if i < len(rscores) else 0.0
        h["rerank_score"] = float(rs)
        rerank_pairs.append(
            {
                "point_id": h.get("id"),
                "collection": h.get("collection"),
                "hybrid_rrf_score": h.get("score"),
                "rerank_score": float(rs),
                "path": (h.get("payload") or {}).get("path")
                or (h.get("payload") or {}).get("source_path"),
            }
        )
    pool.sort(key=lambda x: x["rerank_score"], reverse=True)
    top = pool[: settings.rerank_top_k]

    ctx = format_docs_for_prompt(top)
    user_prompt = f"Question:\n{rewritten}\n\nContext:\n{ctx}"
    user_prompt_stored = user_prompt
    if len(user_prompt_stored) > _USER_PROMPT_MAX:
        user_prompt_stored = user_prompt_stored[:_USER_PROMPT_MAX] + "\n… [truncated for explorer payload]"

    if not top:
        answer = "No relevant documents found."
    else:
        answer = build_answer_non_stream(settings, groq, rewritten, top)

    steps = [
        "User question received (and optional chat history).",
        (
            "Query rewrite (Groq): last turns condensed into one standalone search question."
            if history_used
            else "No history — the raw question is used as the search query."
        ),
        (
            "Router (Groq): classifies the question into 1–2 Qdrant collections "
            "(or uses your source filter / falls back to all collections if JSON parse fails)."
        ),
        "Embedding (BGE-M3): dense vector + lexical sparse vector for the search question.",
        (
            "Hybrid retrieval per routed collection: Qdrant prefetches dense top-N and sparse top-N, "
            "then RRF fusion; capped by top_k_per_collection."
        ),
        "Merge hits from all selected collections; dedupe by (collection, text prefix); sort by RRF score.",
        f"Take top {settings.rerank_pool} for cross-encoder reranking (BGE reranker).",
        f"Rerank with query vs passage pairs; keep top {settings.rerank_top_k} chunks.",
        "Build <doc>…</doc> context and call Groq generator (temperature 0.2) with citation instructions.",
    ]

    return {
        "query_original": question,
        "query_rewritten": rewritten,
        "history_turns_used": len(hist),
        "history_used": history_used,
        "router_collections": cols,
        "router_raw_llm": router_raw,
        "router_fallback_all_collections": router_fallback,
        "embedding_model": settings.embed_model,
        "rerank_model": settings.rerank_model,
        "groq_model": settings.groq_model,
        "settings": {
            "prefetch_limit": settings.prefetch_limit,
            "top_k_per_collection": settings.top_k_per_collection,
            "rerank_pool": settings.rerank_pool,
            "rerank_top_k": settings.rerank_top_k,
            "history_turns_setting": settings.history_turns,
        },
        "per_collection_hits": per_collection,
        "counts": {
            "after_hybrid_merge": merged_count,
            "after_dedupe": deduped_count,
            "after_rrf_score_sort_and_rerank_pool_trim": len(after_rrf_trim),
            "final_context_chunks": len(top),
        },
        "rerank_pool_summaries": after_rrf_trim,
        "rerank_scores_table": rerank_pairs,
        "final_chunks": [
            _hit_summary(h) | {"full_text": h.get("text") or "", "rerank_score": h.get("rerank_score")}
            for h in top
        ],
        "prompt_system": ANSWER_SYSTEM,
        "prompt_user": user_prompt_stored,
        "answer": answer,
        "citations": citations_payload(top),
        "pipeline_steps_explained": steps,
    }
