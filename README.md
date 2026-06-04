# QA Copilot

**Current release: [v1.0.0](VERSION.md)** — Chat, RAG Explorer (debug), Status (paths), KT docs.

**Project root:** always `cd` into **this folder** (`QACopilot` that contains `app.py`, `frontend/`, `.env`).  
Do not run from the parent `...\QACopilot\` folder or from `RAG SYSTEM\QACopilot` (duplicate copy).

**GitHub:** https://github.com/Manjusha3010/QA_Copilot · **Deploy (Vercel UI):** see [DEPLOY.md](DEPLOY.md)

**[plan.md](plan.md)** — architecture (Modular RAG vs [The Testing Academy RAG guide](https://app.thetestingacademy.com/rag#modular)), data layout, phased roadmap.

VWO-focused QA assistant: **Qdrant** (five collections in `backend/`), **BGE-M3** + **bge-reranker-v2-m3**, **Groq**, **React + Vite + Tailwind** UI.

## Run

1. `cd` into this folder (`QACopilot`).
2. Copy `.env.example` to `.env` and set `GROQ_API_KEY` (and optional `GROQ_MODEL`).
3. `pip install -r requirements.txt` — use **Python 3.11–3.13** if `qdrant-client` fails on newer Python.
4. **API:** `.\start.ps1` or `.\.venv\Scripts\python.exe app.py` — **http://127.0.0.1:8843**
5. **UI (dev):** `.\start-ui.ps1` or `cd frontend && npm run dev` — **http://localhost:5173/**  
   Nav: **Chat · RAG Explorer · Status · KT Doc**. Configure data paths on **Status** (saved to `local_paths.json`).

After frontend changes, run `cd frontend && npm run build` so **http://127.0.0.1:8843/** serves the new UI (not a stale `frontend/dist`).

Local source roots: **Status** page or `.env` (`PDFS_DIR`, `JIRA_MD_DIR`, etc. — see `.env.example`).

### Selenium framework repo

Keep the clone **inside this project** under **`data/repos/`** (ignored by git so it is not pushed):

```bash
mkdir data\repos
cd data\repos
git clone https://github.com/PramodDutta/ATB14xSeleniumAdvanceFrameworks.git
cd ..\..
```

Default path for indexing: **`./data/repos/ATB14xSeleniumAdvanceFrameworks`** — set **Selenium repo** in the wizard or `COPILOT_PATH_SELENIUM` in `.env` (see `.env.example`), then **Reindex** so **`source_selenium`** is filled.

Upstream: **[PramodDutta/ATB14xSeleniumAdvanceFrameworks](https://github.com/PramodDutta/ATB14xSeleniumAdvanceFrameworks)**.

### Playwright framework repo

Same layout under **`data/repos/`**:

```bash
cd data\repos
git clone https://github.com/PramodDutta/Advance-Playwright-Framework.git
cd ..\..
```

Default: **`./data/repos/Advance-Playwright-Framework`** → `COPILOT_PATH_PLAYWRIGHT` / wizard **Playwright repo**, then **Reindex** for **`source_playwright`**.

Upstream: **[PramodDutta/Advance-Playwright-Framework](https://github.com/PramodDutta/Advance-Playwright-Framework)**.

### Markdown notes (`data/MD`)

Place **`.md`** files (e.g. `Bug1.md`, `Bug2.md`) under **`data/MD`**. They are indexed into **`source_pdfs`** together with PDFs (`source_type: markdown` in metadata). Default folder: **`./data/MD`** (`COPILOT_PATH_MARKDOWN`). Reindex **pdfs** or **all** after changes.

Your other `data/` assets (CSV, PDF folders) are unchanged; set **PDFs** to e.g. `data/PDF` in the wizard if you want those PDFs indexed too.
