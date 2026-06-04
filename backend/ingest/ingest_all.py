"""Run all five ingesters."""

from __future__ import annotations

from backend.ingest import ingest_jira, ingest_pdfs, ingest_playwright, ingest_selenium, ingest_testcases


def run_all(settings, client, embedder, clear: bool = False) -> dict[str, int]:
    return {
        "selenium_code": ingest_selenium.run(settings, client, embedder, clear),
        "playwright_code": ingest_playwright.run(settings, client, embedder, clear),
        "vwo_testcases": ingest_testcases.run(settings, client, embedder, clear),
        "vwo_docs": ingest_pdfs.run(settings, client, embedder, clear),
        "vwo_bugs": ingest_jira.run(settings, client, embedder, clear),
    }


if __name__ == "__main__":
    import os
    import sys

    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
    from dotenv import load_dotenv

    load_dotenv()
    from backend.lib import embeddings, qdrant_store
    from backend.lib.settings import get_settings

    s = get_settings()
    emb = embeddings.get_embedder(s.embed_model)
    client = qdrant_store.get_client(s)
    qdrant_store.ensure_collections(client)
    clear = "--clear" in sys.argv
    out = run_all(s, client, emb, clear=clear)
    print(out)
