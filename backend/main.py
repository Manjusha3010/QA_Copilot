"""FastAPI QA Copilot — Chapter 9 style: /api/health, /api/chat (SSE), ingest, paths."""

from __future__ import annotations

import json
import os
import traceback
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, List, Literal, Optional

from dotenv import load_dotenv
from fastapi.staticfiles import StaticFiles
from fastapi import Body, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from groq import Groq
from pydantic import BaseModel, Field

load_dotenv()

from backend.ingest import ingest_all
from backend.lib import embeddings, qdrant_store
from backend.lib.collections import ALL_COLLECTIONS, SOURCE_LABELS
from backend.lib import prompts as prompt_lib
from backend.lib.rag_explore import run_rag_explore
from backend.lib.retriever import (
    build_answer_non_stream,
    citations_payload,
    retrieve_pipeline,
)
from backend.lib.settings import get_settings, save_local_paths

APP_VERSION = "1.0.0"

_ROOT = Path(__file__).resolve().parents[1]
os.makedirs(_ROOT / "data", exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    s = get_settings()
    client = qdrant_store.get_client(s)
    qdrant_store.ensure_collections(client)
    app.state.settings = s
    app.state.qdrant = client
    app.state.embedder = None
    app.state.reranker = None
    app.state.groq = Groq(api_key=s.groq_api_key)
    yield


app = FastAPI(title="QA Copilot (Ch9)", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def _kt_no_cache(request: Request, call_next):
    """KT HTML/CSS updates often; avoid stale browser cache on /kt/."""
    response = await call_next(request)
    if request.url.path.startswith("/kt"):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
    return response


def _emb(request: Request):
    if request.app.state.embedder is None:
        request.app.state.embedder = embeddings.get_embedder(request.app.state.settings.embed_model)
    return request.app.state.embedder


def _rerank(request: Request):
    if request.app.state.reranker is None:
        from backend.lib.reranker import get_reranker

        request.app.state.reranker = get_reranker(request.app.state.settings.rerank_model)
    return request.app.state.reranker


def _reload(request: Request):
    request.app.state.settings = get_settings()


class PathsPayload(BaseModel):
    pdfs: Optional[str] = None
    markdown: Optional[str] = None
    selenium: Optional[str] = None
    playwright: Optional[str] = None
    vwo_tests: Optional[str] = None


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatPayload(BaseModel):
    messages: List[ChatMessage] = Field(default_factory=list)
    sources: Optional[List[str]] = None


class QueryPayload(BaseModel):
    query: str = Field(..., min_length=1, max_length=8000)
    mode: Literal["docs", "tests"] = "docs"
    sources: Optional[List[str]] = None
    history: List[ChatMessage] = Field(default_factory=list)


class ExplorePayload(BaseModel):
    query: str = Field(..., min_length=1, max_length=8000)
    sources: Optional[List[str]] = None
    history: List[ChatMessage] = Field(default_factory=list)


@app.get("/api/health")
async def health(request: Request):
    _reload(request)
    client = request.app.state.qdrant
    counts = {}
    for name in ALL_COLLECTIONS:
        try:
            counts[name] = client.count(collection_name=name, exact=True).count
        except Exception:
            counts[name] = 0
    return {"status": "ok", "collections": counts}


@app.get("/api/meta")
async def meta(request: Request):
    _reload(request)
    s = request.app.state.settings
    return {
        "version": APP_VERSION,
        "embed_model": s.embed_model,
        "rerank_model": s.rerank_model,
        "reranker_model": s.rerank_model,
        "groq_model": s.groq_model,
        "collections": [{"id": c, "label": SOURCE_LABELS.get(c, c)} for c in ALL_COLLECTIONS],
        "paths": {
            "pdfs_dir": s.pdfs_dir,
            "jira_md_dir": s.jira_md_dir,
            "selenium_repo_dir": s.selenium_repo_dir,
            "playwright_repo_dir": s.playwright_repo_dir,
            "testcases_csv": s.testcases_csv,
            "pdfs": s.pdfs_dir,
            "markdown": s.jira_md_dir,
            "selenium": s.selenium_repo_dir,
            "playwright": s.playwright_repo_dir,
            "vwo_tests": s.testcases_csv,
        },
    }


@app.post("/api/settings/paths")
async def post_paths(body: PathsPayload, request: Request):
    save_local_paths(
        pdfs=body.pdfs,
        markdown=body.markdown,
        selenium=body.selenium,
        playwright=body.playwright,
        vwo_tests=body.vwo_tests,
    )
    _reload(request)
    return {"ok": True, "paths": (await meta(request))["paths"]}


class IngestPayload(BaseModel):
    clear: bool = False
    collections: Optional[List[str]] = None


@app.post("/api/ingest/all")
async def ingest_all_route(request: Request, clear: bool = False):
    _reload(request)
    s = request.app.state.settings
    try:
        out = ingest_all.run_all(s, request.app.state.qdrant, _emb(request), clear=clear)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, str(e)) from e
    return {"indexed_chunks": out}


@app.post("/api/ingest")
async def ingest_compat(
    request: Request,
    body: Optional[IngestPayload] = Body(default=None),
):
    """Same as `/api/ingest/all`; accepts optional JSON `{ clear, collections }` for the UI."""
    clear = bool(body.clear) if body else False
    return await ingest_all_route(request, clear=clear)


@app.post("/api/rag/explore")
async def rag_explore(body: ExplorePayload, request: Request):
    """Debug trace: rewrite, router, per-collection hits, rerank table, prompts, answer."""
    _reload(request)
    s = request.app.state.settings
    hist = [m.model_dump() for m in body.history]
    if body.sources:
        bad = [x for x in body.sources if x not in ALL_COLLECTIONS]
        if bad:
            raise HTTPException(400, f"Unknown collections: {bad}")
    try:
        out = run_rag_explore(
            s,
            request.app.state.qdrant,
            _emb(request),
            _rerank(request),
            request.app.state.groq,
            body.query,
            hist,
            body.sources,
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, str(e)) from e
    return out


@app.post("/api/query")
async def query_json(body: QueryPayload, request: Request):
    _reload(request)
    s = request.app.state.settings
    hist = [m.model_dump() for m in body.history]
    if body.sources:
        bad = [x for x in body.sources if x not in ALL_COLLECTIONS]
        if bad:
            raise HTTPException(400, f"Unknown collections: {bad}")
    try:
        standalone, chunks, cols = retrieve_pipeline(
            s,
            request.app.state.qdrant,
            _emb(request),
            _rerank(request),
            request.app.state.groq,
            body.query,
            hist,
            body.sources,
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, str(e)) from e
    if not chunks:
        return {
            "standalone_query": standalone,
            "answer": "No relevant documents found.",
            "citations": [],
            "router_collections": cols,
        }
    answer = build_answer_non_stream(s, request.app.state.groq, standalone, chunks)
    return {
        "standalone_query": standalone,
        "answer": answer,
        "citations": citations_payload(chunks),
        "router_collections": cols,
    }


def _sse(obj: dict) -> str:
    return f"data: {json.dumps(obj, ensure_ascii=False)}\n\n"


@app.post("/api/chat")
async def chat_sse(body: ChatPayload, request: Request):
    _reload(request)
    s = request.app.state.settings
    msgs = body.messages
    if not msgs:
        raise HTTPException(400, "messages required")
    latest = msgs[-1].content
    hist = [m.model_dump() for m in msgs[:-1]]

    def stream() -> Any:
        try:
            standalone, chunks, cols = retrieve_pipeline(
                s,
                request.app.state.qdrant,
                _emb(request),
                _rerank(request),
                request.app.state.groq,
                latest,
                hist,
                body.sources,
            )
            yield _sse({"type": "meta", "standalone_query": standalone, "router_collections": cols})
            if not chunks:
                yield _sse({"type": "token", "text": "No relevant documents found."})
                yield _sse({"type": "sources", "citations": []})
                yield "data: [DONE]\n\n"
                return
            ctx = prompt_lib.format_docs_for_prompt(chunks)
            chat_stream = request.app.state.groq.chat.completions.create(
                model=s.groq_model,
                messages=[
                    {"role": "system", "content": prompt_lib.ANSWER_SYSTEM},
                    {"role": "user", "content": f"Question:\n{standalone}\n\nContext:\n{ctx}"},
                ],
                temperature=0.2,
                stream=True,
            )
            for ch in chat_stream:
                delta = ch.choices[0].delta.content or ""
                if delta:
                    yield _sse({"type": "token", "text": delta})
            yield _sse({"type": "sources", "citations": citations_payload(chunks)})
        except Exception as e:
            traceback.print_exc()
            yield _sse({"type": "error", "message": str(e)})
        yield "data: [DONE]\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")


_kt_dir = _ROOT / "KT"
if _kt_dir.is_dir():
    from fastapi.staticfiles import StaticFiles

    app.mount("/kt", StaticFiles(directory=str(_kt_dir), html=True), name="kt")

# Built UI (Chat / Explorer / Status). Rebuild after frontend changes: cd frontend && npm run build
dist = _ROOT / "frontend" / "dist"
if dist.is_dir():
    app.mount("/", StaticFiles(directory=str(dist), html=True), name="spa")


if __name__ == "__main__":
    import uvicorn

    from backend.run_config import api_port

    uvicorn.run("backend.main:app", host="0.0.0.0", port=api_port(), reload=True)
