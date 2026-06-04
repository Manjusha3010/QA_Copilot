"""Ingest VWO testcase CSV → vwo_testcases."""

from __future__ import annotations

from pathlib import Path

from backend.ingest._common import upsert_text_chunks
from backend.lib import chunking_text
from backend.lib.collections import VWO_TESTCASES


def run(settings, client, embedder, clear: bool = False) -> int:
    path = Path(settings.testcases_csv)
    pairs = chunking_text.chunk_testcases_csv(path)
    return upsert_text_chunks(settings, client, embedder, VWO_TESTCASES, pairs, clear)
