"""Ingest PDFs with PyMuPDF → vwo_docs + skip report."""

from __future__ import annotations

from pathlib import Path

from backend.ingest._common import upsert_text_chunks
from backend.lib import chunking_md_pdf
from backend.lib.collections import VWO_DOCS
from backend.lib.settings import Settings


def run(settings: Settings, client, embedder, clear: bool = False) -> int:
    root = Path(settings.pdfs_dir)
    report: dict = {"skipped_pages": [], "errors": []}
    pairs = []
    if root.is_dir():
        for pdf in root.rglob("*.pdf"):
            pairs.extend(chunking_md_pdf.chunk_pdf_pymupdf(pdf, report))
    chunking_md_pdf.write_skip_report(Path(__file__).resolve().parents[2], report)
    return upsert_text_chunks(settings, client, embedder, VWO_DOCS, pairs, clear)
