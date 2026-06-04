"""Ingest Selenium Java repo → selenium_code."""

from __future__ import annotations

from pathlib import Path
from typing import Generator, Optional, Set

from backend.ingest._common import upsert_text_chunks
from backend.lib import chunking_code
from backend.lib.collections import SELENIUM_CODE

SKIP = {
    ".git",
    "node_modules",
    "target",
    "build",
    ".idea",
    "__pycache__",
    ".gradle",
}


def _walk(root: Path) -> Generator[Path, None, None]:
    if not root.is_dir():
        return
    for p in root.rglob("*.java"):
        if any(x in p.parts for x in SKIP):
            continue
        yield p


def run(settings, client, embedder, clear: bool = False) -> int:
    root = Path(settings.selenium_repo_dir)
    pairs = []
    for f in _walk(root):
        pairs.extend(chunking_code.chunk_java_file(f))
    return upsert_text_chunks(settings, client, embedder, SELENIUM_CODE, pairs, clear)
