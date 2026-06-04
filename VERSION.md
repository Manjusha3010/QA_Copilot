# QA Copilot — v1.0.0

**Release date:** 2026-05-15  
**Status:** Baseline for local Modular RAG — wizard, ingest, ask with citations.

## What works in v1.0.0

- **Backend** (`python app.py`) on port **8843** — health, meta, paths, ingest, query, RAG explore
- **Frontend** (`npm run dev`) on port **5173** — setup wizard, reindex, ask (docs/tests mode)
- **Five Qdrant collections:** `selenium_code`, `playwright_code`, `vwo_testcases`, `vwo_docs`, `vwo_bugs`
- **Hybrid retrieval:** BGE-M3 dense + sparse, RRF merge, BGE reranker, Groq router/answer
- **KT docs** at `http://127.0.0.1:8843/kt/`
- **Path config:** `.env` + `local_paths.json` (wizard); `.data/` typo auto-corrected to `./data/`

## Default data paths

| Setting | Path |
|---------|------|
| PDFs | `./data/PDF` |
| Markdown | `./data/MD` |
| Selenium | `./data/repos/ATB14xSeleniumAdvanceFrameworks` |
| Playwright | `./data/repos/Advance-Playwright-Framework` |
| VWO testcases | `./data/CSV/testcases_vwo_100.csv` (100 rows) |

## Run (every session)

```powershell
cd "D:\manjusha\AITester2xBlueprint\RAG SYSTEM\QACopilot"
.\.venv\Scripts\python.exe app.py

# second terminal
cd frontend
npm run dev
```

After path or CSV changes: **Reindex all** once, then confirm `GET http://127.0.0.1:8843/api/health` shows all collections &gt; 0.

## V1 acceptance checklist

- [ ] Python **3.11** venv; `pip install -r requirements.txt` (`transformers` &lt; 5)
- [ ] `GROQ_API_KEY` in `.env`
- [ ] `local_paths.json` uses `./data/...` and CSV **file** path (not a folder)
- [ ] `testcases_vwo_100.csv` has data rows (not header-only)
- [ ] Reindex completes; health: `vwo_testcases` ≈ **100**, others &gt; 0
- [ ] Ask returns answer + citations (no `prepare_for_model` error)

## Known limitations (deferred to v2+)

- Wizard “done” state is not persisted across browser refresh
- Reindex uses `clear: false` (does not wipe collections before reload)
- No per-collection ingest from UI
- Full `testcases_vwo.csv` (~5000 rows) not default; use path change + reindex if needed

## Freeze this release (optional Git)

```powershell
cd QACopilot
git init
git add .
git commit -m "QA Copilot v1.0.0 — local modular RAG baseline"
git tag -a v1.0.0 -m "Version 1.0.0 baseline"
```

Or copy the folder to `QACopilot-v1.0.0-backup` without Git.

## Version 2

Plan new work from tag/backup `v1.0.0`. Examples: persist wizard, reindex progress, index full CSV, Docker deploy.
