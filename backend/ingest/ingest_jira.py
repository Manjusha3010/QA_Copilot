"""Ingest JIRA markdown exports → vwo_bugs."""

from __future__ import annotations

from pathlib import Path

from backend.ingest._common import upsert_text_chunks
from backend.lib import chunking_md_pdf
from backend.lib.collections import VWO_BUGS
from backend.lib.settings import Settings


def run(settings: Settings, client, embedder, clear: bool = False) -> int:
    root = Path(settings.jira_md_dir)
    pairs = []
    if root.is_dir():
        for md in root.rglob("*.md"):
            pairs.extend(chunking_md_pdf.chunk_jira_md(md))
    return upsert_text_chunks(settings, client, embedder, VWO_BUGS, pairs, clear)
