# QA Copilot — plan

## Goal

A **QA co-pilot** for app.vwo.com and related automation: answer from **PDFs, Markdown notes, Selenium repo, Playwright repo, and VWO tests**, with **citations** and **Groq** as the generator.

---

## Teacher Chapter 9 plan vs this repo

**Short answer:** you are **partially** following the same *intent* (multi-source QA RAG, Groq, Qdrant, BGE-M3 + reranker, React+Vite+Tailwind, clones, cited answers), but **not** the same *spec*. This folder is an **MVP / sibling layout** (`QACopilot/`), not the canonical **`Chapter_09_Project_QACopilot/`** tree (`backend/`, `frontend/`, five named collections, hybrid+RRF, LLM router, SSE, etc.).

### Aligned (same direction)

| Teacher spec | This repo (`QACopilot`) |
|--------------|-------------------------|
| FastAPI backend | Yes — root `app.py` |
| Qdrant + bge-m3 + bge-reranker-v2-m3 | Yes — `copilot/models_cache.py`, `qdrant_ops.py` |
| Groq LLM | Yes — configurable `GROQ_MODEL` (default is not locked to `openai/gpt-oss-120b`; set in `.env`) |
| React + Vite + Tailwind | Yes — `frontend/` |
| Selenium + Playwright upstream repos | Same GitHub projects; clones live under **`data/repos/`** (teacher: `data/selenium_repo/`, `data/playwright_repo/`) |
| Markdown under `data` | Yes — **`data/MD`** → indexed (teacher: `data/md/` JIRA bugs, often `Bug_VWO_*.md`) |
| PDFs under `data` | Supported via path (e.g. `data/PDF`) — teacher: `data/pdf/` |
| Citations in API response | Yes — `citations` payload; UI lists sources (not full Ch9 citation UX) |
| Modular “router → retrieve → rerank → generate” idea | Yes — see [Modular RAG](#rag-type-the-testing-academy-taxonomy) below |

### Partially aligned (different shape)

| Teacher spec | Gap in this repo |
|--------------|------------------|
| **5 collections** (`selenium_code`, `playwright_code`, `vwo_testcases`, `vwo_docs`, `vwo_bugs`) | **4 collections** (`source_selenium`, `source_playwright`, `source_pdfs`, `source_vwo_tests`); **PDFs + Markdown share `source_pdfs`** with `source_type` |
| **Hybrid dense + sparse + RRF**, `k=60` → rerank → **top-4** to LLM | **Dense-only** Qdrant search; rerank on pooled hits; **no** sparse vectors, **no** RRF; top-k knobs differ (`CONTEXT_CHUNKS`, etc.) |
| **LLM intent-router** (Groq → 1–2 collections) | **Keyword/heuristic router** in `copilot/retrieval.py` |
| **AST-aware chunking** (tree-sitter Java + TS) | **Recursive text splitter** on code files (no tree-sitter) |
| **CSV testcases** row-aware (`testcases_vwo_100.csv` schema) | **No dedicated CSV ingest** yet; `source_vwo_tests` walks code-style paths only |
| **PyMuPDF** PDFs, empty skip + `_skip_report.json` | **pypdf** + chunking; **no** skip report file |
| **JIRA MD** header metadata (`jira_id`, status, …) | Plain **markdown file** chunking; **no** JIRA header parser |
| **`/api/chat` SSE** streaming | **`POST /api/query`** JSON, **non-streaming** |
| **Multi-turn** + history-condensing **query rewriter** | **Single-turn** queries (no session memory rewriter) |
| **3-pane UI**: sidebar filters, chat, citation cards with **inline [n]** chips | **Wizard + simpler co-pilot** view; no SSE, no `[n]` chip protocol |
| **Ports** 8000 API / 5173 UI | **8843** API default / **5173** UI (`QACOPILOT_API_PORT`, `VITE_API_PROXY`) |
| **Chapter layout** (`backend/main.py`, `ingest/*`, `lib/*`, `CLAUDE.md`) | **Flat** `app.py` + `copilot/*`; **no** `CLAUDE.md` |
| **Reuse Chapter 8** Advance libs | **Not ported**; FlagEmbedding used directly here |

### Not following yet (if you need 100% parity)

1. Split **`vwo_docs`** vs **`vwo_bugs`** and rename collections to match teacher names.  
2. Add **CSV testcase** ingest (`data/csv/…`) with row-aware chunks + TC metadata.  
3. **Hybrid** Qdrant (named vectors dense+sparse), **RRF** fusion, then rerank; tune **top-12 → top-4**.  
4. Replace keyword router with **Groq router** (+ optional user override only).  
5. **tree-sitter** chunking for `.java` and `.ts`/`.js`.  
6. **PyMuPDF** + skip report for PDFs.  
7. **JIRA markdown** parser for `Bug_VWO_*.md`.  
8. **`/api/chat` SSE** + **query rewriter** with last **N** turns.  
9. Frontend **ChatPane / SourcePanel / SourceFilter / IngestStatus** + inline **`[n]`** + scroll-to-source.  
10. Add **`CLAUDE.md`**, align **`README.md`** to chapter style (optional mermaid), match **env var names** and **`qdrant_data/`** naming if required by course.

**Bottom line:** treat this repo as a **working subset** you can **grow into Chapter 9** by porting the teacher’s modules and directory layout—or re-scaffold into `Chapter_09_Project_QACopilot/` and migrate ingestion/router/UI as phases.

---

## RAG type (The Testing Academy taxonomy)

Reference: [RAG tutorial — Modular RAG](https://app.thetestingacademy.com/rag#modular).

This project is best described as **Modular RAG**: separate pipeline modules (router → retriever(s) → reranker → generator), not a single monolithic “naive” retrieve-then-generate only.

| Module (Modular RAG) | Implementation today | Notes |
|----------------------|-------------------------|--------|
| **Router** | Keyword / heuristic routing in `copilot/retrieval.py` (`decide_collections`) | Chooses which **Qdrant collections** to hit. **Not** an LLM classifier (their docs often show an LLM router). |
| **Retriever** | Per-collection **dense vector** search in **Qdrant** | One collection per source (`source_pdfs`, `source_selenium`, `source_playwright`, `source_vwo_tests`). |
| **Reranker** | **BAAI/bge-reranker-v2-m3** (FlagEmbedding) | Re-scores pooled hits before context packing. |
| **Generator** | **Groq** (`GROQ_MODEL` in `.env`) | Grounded prompt; “don’t know” when context is weak. |
| **Memory** | Not implemented | Queries are effectively **stateless** (no chat buffer / summary memory). |
| **Guardrails** | Prompt-level only | No NeMo-style guardrail service; can be extended later. |

**Not** the same as their **Naive RAG** (single store, no rerank, no routing). **Partial overlap** with **Advanced RAG** (we use reranking; we do **not** use HyDE, parent–child retrieval, or contextual compression as in their Advanced section).

---

## Data layout

| Asset | Location (default) | Vector collection | Upstream |
|--------|---------------------|-------------------|----------|
| Selenium framework | `./data/repos/ATB14xSeleniumAdvanceFrameworks` | `source_selenium` | [ATB14xSeleniumAdvanceFrameworks](https://github.com/PramodDutta/ATB14xSeleniumAdvanceFrameworks) |
| Playwright framework | `./data/repos/Advance-Playwright-Framework` | `source_playwright` | [Advance-Playwright-Framework](https://github.com/PramodDutta/Advance-Playwright-Framework) |
| Markdown / bug notes | `./data/MD` (`COPILOT_PATH_MARKDOWN`) | `source_pdfs` (`source_type: markdown`) | Local files |
| PDFs / docs | `COPILOT_PATH_PDFS` (e.g. `./data/PDF`) | `source_pdfs` (`source_type: pdf`) | Local files |
| VWO tests | `COPILOT_PATH_VWO_TESTS` | `source_vwo_tests` | User-provided path |

Clones under `data/repos/` are **gitignored** (see `data/repos/README.md`).

---

## Tech stack

- **API:** FastAPI (`app.py`)
- **Vector DB:** Qdrant (local path or `QDRANT_URL`)
- **Embeddings:** BAAI/bge-m3 (dense)
- **Reranker:** BAAI/bge-reranker-v2-m3
- **LLM:** Groq
- **UI:** React + Vite + Tailwind (`frontend/`)

---

## Configuration

- **Env:** copy `.env.example` → `.env` (at minimum `GROQ_API_KEY`).
- **Paths:** UI wizard or `local_paths.json` (see `POST /api/settings/paths`); merges with env-backed `Settings` in `copilot/config.py`.
- **Reindex:** UI “Reindex all” or `POST /api/ingest` after changing paths or documents.

---

## Phased roadmap

### Phase 1 — Done (MVP)

- **Subset of teacher Chapter 9 Phase 1:** four Qdrant collections + ingestion for code, PDFs, Markdown, tests (`copilot/ingest.py`) — not five collections, not CSV/JIRA parsers, not tree-sitter.
- Keyword router + merge + BGE rerank + Groq answer + citations API (`/api/query`).
- React wizard + co-pilot UI; `data/repos` + `data/MD` defaults documented in `README.md`.

### Phase 2 — Stronger Modular RAG

- **LLM or embedding router:** optional Groq call to classify query → collections (fallback to today’s keyword router).
- **Hybrid retrieval:** BM25 or keyword index alongside vectors for selectors, file paths, JIRA keys.
- **Eval set:** 20–50 questions with expected sources to regression-test retrieval.

### Phase 3 — Product hardening

- **Conversation memory:** last N turns or summarized history passed into generator.
- **Guardrails:** structured output checks, PII redaction, or a small rules engine if needed.
- **Observability:** request IDs, latency metrics, retrieval scores logged per query.

### Phase 4 — Ops

- Optional **remote Qdrant**; CI job to reindex on schedule; model pin versions in lockfile or container image.

---

## How to run (short)

1. `cd QACopilot`
2. `pip install -r requirements.txt` (Python **3.11–3.13** recommended for `qdrant-client` / protobuf stability).
3. `python app.py` → API `http://127.0.0.1:8843` (or set `QACOPILOT_API_PORT`)
4. `cd frontend && npm install && npm run dev` **or** `npm run build` and serve `frontend/dist` via FastAPI.

Details stay in [README.md](README.md).
