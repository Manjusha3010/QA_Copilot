# Local clones under `data/repos`

Clone frameworks **here** so paths stay under `data/`.

## Selenium

```bash
cd data/repos
git clone https://github.com/PramodDutta/ATB14xSeleniumAdvanceFrameworks.git
cd ../..
```

`COPILOT_PATH_SELENIUM=./data/repos/ATB14xSeleniumAdvanceFrameworks`

## Playwright

```bash
cd data/repos
git clone https://github.com/PramodDutta/Advance-Playwright-Framework.git
cd ../..
```

`COPILOT_PATH_PLAYWRIGHT=./data/repos/Advance-Playwright-Framework`

Then **Reindex** from the UI (or `POST /api/ingest`). Clone folders are gitignored.

| Upstream | URL |
|----------|-----|
| Selenium | https://github.com/PramodDutta/ATB14xSeleniumAdvanceFrameworks |
| Playwright | https://github.com/PramodDutta/Advance-Playwright-Framework |

## Markdown notes (`data/MD`)

Bug write-ups and other **`.md`** files under **`./data/MD`** (default `COPILOT_PATH_MARKDOWN`) are indexed into the same **`source_pdfs`** collection as PDFs (metadata `source_type: markdown`). Add or edit files there and reindex **pdfs** (or **all**).
