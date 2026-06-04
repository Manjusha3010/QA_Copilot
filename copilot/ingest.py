from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Tuple

from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

from copilot.config import Settings
from copilot.constants import (
    COLLECTION_PDFS,
    COLLECTION_PLAYWRIGHT,
    COLLECTION_SELENIUM,
    COLLECTION_VWO_TESTS,
)
from copilot import models_cache
from copilot import qdrant_ops

CODE_EXT = {".py", ".ts", ".tsx", ".js", ".jsx", ".java", ".cs", ".kt", ".go", ".rb", ".feature"}
SKIP_DIR_NAMES = {
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    "dist",
    "build",
    ".idea",
    ".gradle",
    "target",
}


def _iter_files(root: Path, extensions: Optional[set]) -> Generator[Path, None, None]:
    if not root.is_dir():
        return
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        parts = set(p.parts)
        if parts & SKIP_DIR_NAMES:
            continue
        if any(d in SKIP_DIR_NAMES for d in p.parts):
            continue
        if extensions and p.suffix.lower() not in extensions:
            continue
        yield p


def _pdf_chunks(path: Path) -> List[Tuple[str, Dict[str, Any]]]:
    out: List[Tuple[str, Dict[str, Any]]] = []
    try:
        reader = PdfReader(str(path))
    except Exception:
        return out
    full_text_len = 0
    for i, page in enumerate(reader.pages):
        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""
        full_text_len += len(text.strip())
        meta = {
            "source_type": "pdf",
            "path": str(path),
            "page": i,
            "doc_title": path.stem,
            "doc_quality": "low" if len(text.strip()) < 40 else "normal",
        }
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=900,
            chunk_overlap=120,
            length_function=len,
        )
        for chunk in splitter.split_text(text):
            if chunk.strip():
                out.append((chunk.strip(), meta))
    if not out and full_text_len < 20:
        out.append(
            (
                f"(Minimal extract) File: {path.name}. Text extraction yielded almost no content.",
                {
                    "source_type": "pdf",
                    "path": str(path),
                    "page": 0,
                    "doc_title": path.stem,
                    "doc_quality": "low",
                },
            )
        )
    return out


def _markdown_chunks(path: Path) -> List[Tuple[str, Dict[str, Any]]]:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    if not text.strip():
        return []
    meta_base: Dict[str, Any] = {
        "source_type": "markdown",
        "path": str(path),
        "page": 0,
        "doc_title": path.stem,
        "doc_quality": "low" if len(text.strip()) < 30 else "normal",
    }
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=900,
        chunk_overlap=120,
        length_function=len,
    )
    return [(c.strip(), {**meta_base}) for c in splitter.split_text(text) if c.strip()]


def _code_chunks(path: Path, framework: str) -> List[Tuple[str, Dict[str, Any]]]:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    if not text.strip():
        return []
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1200,
        chunk_overlap=150,
        length_function=len,
        separators=["\nclass ", "\ndef ", "\npublic class ", "\n@Test", "\n    @", "\n\n", "\n"],
    )
    base_meta = {
        "source_type": "code",
        "framework": framework,
        "path": str(path),
        "language": path.suffix.lower().lstrip(".") or "unknown",
    }
    out: List[Tuple[str, Dict[str, Any]]] = []
    for chunk in splitter.split_text(text):
        if chunk.strip():
            out.append((chunk.strip(), {**base_meta}))
    return out


def _maybe_test_case_chunks(path: Path) -> List[Tuple[str, Dict[str, Any]]]:
    """Prefer scenario-sized chunks for Gherkin; otherwise code-style chunks with test metadata."""
    if path.suffix.lower() == ".feature":
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return []
        scenarios = re.split(r"(?=^Feature:|^Scenario Outline:|^Scenario:)", text, flags=re.MULTILINE)
        out: List[Tuple[str, Dict[str, Any]]] = []
        for i, block in enumerate(s for s in scenarios if s.strip()):
            title = ""
            m = re.search(r"^(Scenario(?: Outline)?:\s*.+)$", block, re.MULTILINE)
            if m:
                title = m.group(1).strip()
            out.append(
                (
                    block.strip(),
                    {
                        "source_type": "test",
                        "path": str(path),
                        "case_id": f"{path.stem}:{i}",
                        "title": title or path.stem,
                        "line_span": "0",
                    },
                )
            )
        return out if out else _code_chunks(path, "vwo_tests")
    return _code_chunks(path, "vwo_tests")


def _embed_and_upsert(
    settings: Settings,
    client,
    embedder,
    collection: str,
    pairs: List[Tuple[str, Dict[str, Any]]],
    batch_size: int = 16,
) -> int:
    if not pairs:
        return 0
    total = 0
    for i in range(0, len(pairs), batch_size):
        slice_pairs = pairs[i : i + batch_size]
        batch_texts = [t for t, _ in slice_pairs]
        vecs = models_cache.encode_dense(embedder, batch_texts)
        payloads = [{"text": t, **m} for t, m in slice_pairs]
        qdrant_ops.upsert_chunks(client, collection, vecs, payloads)
        total += len(slice_pairs)
    return total


def ingest_pdfs(settings: Settings, client, embedder, clear: bool = False) -> int:
    pairs: List[Tuple[str, Dict[str, Any]]] = []

    if settings.path_pdfs:
        root = Path(settings.path_pdfs)
        if root.is_dir():
            for pdf in _iter_files(root, {".pdf"}):
                pairs.extend(_pdf_chunks(pdf))

    md_dir: Optional[Path] = None
    if settings.path_markdown and str(settings.path_markdown).strip():
        mp = Path(settings.path_markdown.strip())
        if mp.is_dir():
            md_dir = mp

    if not pairs and not md_dir:
        return 0

    if md_dir:
        for md in _iter_files(md_dir, {".md", ".markdown"}):
            pairs.extend(_markdown_chunks(md))

    if not pairs:
        return 0

    if clear and qdrant_ops.collection_exists(client, COLLECTION_PDFS):
        client.delete_collection(COLLECTION_PDFS)
        qdrant_ops.ensure_collections(client)

    return _embed_and_upsert(settings, client, embedder, COLLECTION_PDFS, pairs)


def ingest_selenium(settings: Settings, client, embedder, clear: bool = False) -> int:
    if not settings.path_selenium:
        return 0
    root = Path(settings.path_selenium)
    if clear and qdrant_ops.collection_exists(client, COLLECTION_SELENIUM):
        client.delete_collection(COLLECTION_SELENIUM)
        qdrant_ops.ensure_collections(client)
    pairs: List[Tuple[str, Dict[str, Any]]] = []
    for f in _iter_files(root, CODE_EXT):
        for text, meta in _code_chunks(f, "selenium"):
            meta = {**meta, "repo": root.name}
            pairs.append((text, meta))
    return _embed_and_upsert(settings, client, embedder, COLLECTION_SELENIUM, pairs)


def ingest_playwright(settings: Settings, client, embedder, clear: bool = False) -> int:
    if not settings.path_playwright:
        return 0
    root = Path(settings.path_playwright)
    if clear and qdrant_ops.collection_exists(client, COLLECTION_PLAYWRIGHT):
        client.delete_collection(COLLECTION_PLAYWRIGHT)
        qdrant_ops.ensure_collections(client)
    pairs: List[Tuple[str, Dict[str, Any]]] = []
    for f in _iter_files(root, CODE_EXT):
        for text, meta in _code_chunks(f, "playwright"):
            meta = {**meta, "repo": root.name}
            pairs.append((text, meta))
    return _embed_and_upsert(settings, client, embedder, COLLECTION_PLAYWRIGHT, pairs)


def ingest_vwo_tests(settings: Settings, client, embedder, clear: bool = False) -> int:
    if not settings.path_vwo_tests:
        return 0
    root = Path(settings.path_vwo_tests)
    if clear and qdrant_ops.collection_exists(client, COLLECTION_VWO_TESTS):
        client.delete_collection(COLLECTION_VWO_TESTS)
        qdrant_ops.ensure_collections(client)
    pairs: List[Tuple[str, Dict[str, Any]]] = []
    for f in _iter_files(root, CODE_EXT):
        for text, meta in _maybe_test_case_chunks(f):
            meta = {**meta, "repo": root.name}
            pairs.append((text, meta))
    return _embed_and_upsert(settings, client, embedder, COLLECTION_VWO_TESTS, pairs)


def ingest_uploaded_pdf(settings, client, embedder, file_path: Path, original_name: str) -> int:
    pairs = _pdf_chunks(file_path)
    for text, meta in pairs:
        meta["source"] = original_name
    return _embed_and_upsert(settings, client, embedder, COLLECTION_PDFS, pairs)
