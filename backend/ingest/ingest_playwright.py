"""Ingest Playwright TS/JS repo → playwright_code."""

from __future__ import annotations

from pathlib import Path
from typing import Generator

from backend.ingest._common import upsert_text_chunks
from backend.lib import chunking_code
from backend.lib.collections import PLAYWRIGHT_CODE

SKIP = {
    ".git",
    "node_modules",
    "dist",
    "build",
    ".idea",
    "__pycache__",
}
EXT = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"}


def _walk(root: Path) -> Generator[Path, None, None]:
    if not root.is_dir():
        return
    for p in root.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in EXT:
            continue
        if any(x in p.parts for x in SKIP):
            continue
        yield p


def run(settings, client, embedder, clear: bool = False) -> int:
    root = Path(settings.playwright_repo_dir)
    pairs = []
    for f in _walk(root):
        pairs.extend(chunking_code.chunk_ts_js_file(f))
    return upsert_text_chunks(settings, client, embedder, PLAYWRIGHT_CODE, pairs, clear)
