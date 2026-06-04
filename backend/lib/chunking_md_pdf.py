"""PyMuPDF for PDFs; markdown with optional JIRA-style header parse."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

from langchain_text_splitters import RecursiveCharacterTextSplitter


def chunk_pdf_pymupdf(path: Path, skip_report: dict) -> List[Tuple[str, Dict[str, Any]]]:
    out: List[Tuple[str, Dict[str, Any]]] = []
    try:
        import fitz  # PyMuPDF
    except ImportError:
        skip_report.setdefault("errors", []).append(f"PyMuPDF not installed: {path.name}")
        return out
    try:
        doc = fitz.open(path)
    except Exception as e:
        skip_report.setdefault("errors", []).append(f"{path.name}: {e}")
        return out
    for i in range(len(doc)):
        page = doc.load_page(i)
        text = page.get_text() or ""
        if len(text.strip()) < 50:
            skip_report.setdefault("skipped_pages", []).append(
                {"file": str(path), "page": i + 1, "chars": len(text.strip())}
            )
            continue
        meta = {
            "source_type": "pdf",
            "path": str(path),
            "source_path": str(path),
            "page": i,
            "doc_title": path.stem,
            "section": "",
        }
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=800, chunk_overlap=120, length_function=len
        )
        for chunk in splitter.split_text(text):
            if chunk.strip():
                out.append((chunk.strip(), {**meta}))
    doc.close()
    return out


_HEADER_PATTERNS = {
    "jira_id": re.compile(r"^(?:JIRA|Issue|Key)\s*[:#]\s*(.+)$", re.I | re.M),
    "status": re.compile(r"^Status\s*:\s*(.+)$", re.I | re.M),
    "priority": re.compile(r"^Priority\s*:\s*(.+)$", re.I | re.M),
    "reporter": re.compile(r"^Reporter\s*:\s*(.+)$", re.I | re.M),
    "assignee": re.compile(r"^Assignee\s*:\s*(.+)$", re.I | re.M),
    "labels": re.compile(r"^Labels?\s*:\s*(.+)$", re.I | re.M),
    "created": re.compile(r"^Created\s*:\s*(.+)$", re.I | re.M),
    "updated": re.compile(r"^Updated\s*:\s*(.+)$", re.I | re.M),
    "summary": re.compile(r"^Summary\s*:\s*(.+)$", re.I | re.M),
}


def parse_jira_markdown(path: Path) -> Tuple[Dict[str, Any], str]:
    raw = path.read_text(encoding="utf-8", errors="replace")
    meta: Dict[str, Any] = {k: "" for k in _HEADER_PATTERNS}
    for k, pat in _HEADER_PATTERNS.items():
        m = pat.search(raw)
        if m:
            meta[k] = m.group(1).strip()
    if not meta.get("jira_id"):
        m = re.match(r"^#\s*([A-Z]+-\d+)", raw)
        if m:
            meta["jira_id"] = m.group(1)
    body = raw
    for pat in _HEADER_PATTERNS.values():
        body = pat.sub("", body)
    body = re.sub(r"^---+\s*$", "", body, flags=re.M).strip()
    return meta, body


def chunk_jira_md(path: Path) -> List[Tuple[str, Dict[str, Any]]]:
    try:
        hdr, body = parse_jira_markdown(path)
    except OSError:
        return []
    if not body.strip():
        return []
    meta_base = {
        "source_type": "jira_md",
        "path": str(path),
        "source_path": str(path),
        **{k: v for k, v in hdr.items() if v},
    }
    if len(body) <= 1500:
        return [(body.strip(), meta_base)]
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500, chunk_overlap=100, length_function=len
    )
    return [(c.strip(), {**meta_base, "chunk_part": i}) for i, c in enumerate(splitter.split_text(body)) if c.strip()]


def write_skip_report(root: Path, report: dict) -> None:
    p = root / "data" / "_skip_report.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(report, indent=2), encoding="utf-8")
