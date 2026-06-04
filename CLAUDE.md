# QA Copilot (Chapter 9) — for Claude / Cursor sessions

## Run (from this folder only — `...\QACopilot\QACopilot\`)

Never run from parent `...\QACopilot\` or duplicate `RAG SYSTEM\QACopilot`.

```powershell
.\start.ps1       # API → http://127.0.0.1:8843
.\start-ui.ps1    # UI  → http://localhost:5173 (Chat · RAG Explorer · Status · KT Doc)
```

Paths / reindex: **Status** and **Chat** in the UI — not the legacy blocking wizard (removed).

If port 8843 serves an old wizard UI, rebuild: `cd frontend && npm run build`.

Single ingest modules: `python -m backend.ingest.ingest_selenium` (add `if __name__` blocks if missing).

## Architecture

- **5 Qdrant collections:** `selenium_code`, `playwright_code`, `vwo_testcases`, `vwo_docs`, `vwo_bugs` (`backend/lib/collections.py`).
- **Hybrid vectors:** dense + sparse (`bge-m3`), RRF fusion per collection; dense-only fallback if local Qdrant rejects prefetch (`backend/lib/qdrant_store.py`).
- **Router:** Groq JSON classifier → 1–2 collections (`backend/lib/router.py`). User override via `sources` on `/api/query` or `/api/chat`.
- **Retriever:** optional query rewrite from last N turns → route → hybrid search → pool → `bge-reranker-v2-m3` → top-4 (`backend/lib/retriever.py`).
- **API:** FastAPI in `backend/main.py` — `/api/health` (counts), `/api/meta`, `/api/settings/paths`, `/api/ingest/all`, `/api/ingest`, `/api/query` (JSON), `/api/rag/explore`, `/api/chat` (SSE: `meta`, `token`, `sources`, `[DONE]`). Static KT pages: `/kt/`.

## Data paths (env / `local_paths.json`)

| Env | Purpose |
|-----|---------|
| `SELENIUM_REPO_DIR` | `./data/selenium_repo` |
| `PLAYWRIGHT_REPO_DIR` | `./data/playwright_repo` |
| `TESTCASES_CSV` | `./data/csv/testcases_vwo_100.csv` |
| `PDFS_DIR` | `./data/pdf` |
| `JIRA_MD_DIR` | `./data/MD` (default; teacher uses `data/md`) |

Wizard JSON keys still: `selenium`, `playwright`, `vwo_tests`, `pdfs`, `markdown` → merged into the above.

## Adding a 6th source

1. Add collection name in `backend/lib/collections.py` + `ensure_collections`.
2. New `backend/ingest/ingest_<x>.py` + call from `backend/ingest/ingest_all.py`.
3. Extend `ROUTER_SYSTEM` in `backend/lib/router.py` with the new label.

## Pitfalls

- **Qdrant file mode:** avoid running two processes writing the same `QDRANT_PATH` simultaneously; use `QDRANT_URL` for server mode if ingesting while API serves.
- **First `bge-m3` load:** large model download.
- **tree-sitter-languages:** required for AST-ish splits; falls back to recursive splitter if import/parsing fails.
- **Python 3.11–3.13** recommended for `qdrant-client` / protobuf stability.

## Legacy

Older `copilot/` tree (4 collections) is deprecated; use `backend.main:app` via `python app.py` — default port **8843** (`backend/run_config.py`, overridable with `QACOPILOT_API_PORT`).
