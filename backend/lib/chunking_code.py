"""Code chunking: prefer tree-sitter-languages; else recursive split."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Tuple

from langchain_text_splitters import RecursiveCharacterTextSplitter


def _fallback(path: Path, framework: str) -> List[Tuple[str, Dict[str, Any]]]:
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
        separators=[
            "\nclass ",
            "\npublic class ",
            "\ninterface ",
            "\ndef ",
            "\nfunction ",
            "\nexport ",
            "\ntest(",
            "\n\n",
            "\n",
        ],
    )
    ext = path.suffix.lower().lstrip(".") or "txt"
    base: Dict[str, Any] = {
        "source_type": "code",
        "framework": framework,
        "path": str(path),
        "source_path": str(path),
        "language": ext,
        "symbol": "",
        "kind": "chunk",
        "start_line": 0,
        "end_line": 0,
        "test_title": "",
    }
    return [(c.strip(), {**base}) for c in splitter.split_text(text) if c.strip()]


def _walk_tree(parser, text: str, framework: str, path: Path, node_types: tuple) -> List[Tuple[str, Dict[str, Any]]]:
    tree = parser.parse(bytes(text, "utf8"))
    lines = text.splitlines()
    out: List[Tuple[str, Dict[str, Any]]] = []

    def walk(node):
        if node.type in node_types:
            sr, _ = node.start_point
            er, _ = node.end_point
            snippet = "\n".join(lines[sr : er + 1])
            if len(snippet.strip()) < 15:
                return
            kind = "method" if "method" in node.type or "constructor" in node.type else "class"
            out.append(
                (
                    snippet.strip(),
                    {
                        "source_type": "code",
                        "framework": framework,
                        "path": str(path),
                        "source_path": str(path),
                        "language": path.suffix.lower().lstrip(".") or "java",
                        "symbol": node.type,
                        "kind": kind,
                        "start_line": sr + 1,
                        "end_line": er + 1,
                        "test_title": "",
                    },
                )
            )
        for c in node.children:
            walk(c)

    walk(tree.root_node)
    return out


def chunk_java_file(path: Path) -> List[Tuple[str, Dict[str, Any]]]:
    try:
        from tree_sitter_languages import get_parser

        parser = get_parser("java")
        text = path.read_text(encoding="utf-8", errors="replace")
        hits = _walk_tree(
            parser,
            text,
            "selenium",
            path,
            ("method_declaration", "constructor_declaration", "class_declaration", "interface_declaration"),
        )
        if hits:
            return hits
    except Exception:
        pass
    return _fallback(path, "selenium")


def chunk_ts_js_file(path: Path) -> List[Tuple[str, Dict[str, Any]]]:
    try:
        from tree_sitter_languages import get_parser

        lang = "typescript" if path.suffix.lower() in (".ts", ".tsx") else "javascript"
        parser = get_parser(lang)
        text = path.read_text(encoding="utf-8", errors="replace")
        hits = _walk_tree(
            parser,
            text,
            "playwright",
            path,
            (
                "function_declaration",
                "method_definition",
                "class_declaration",
                "lexical_declaration",
                "export_statement",
            ),
        )
        if hits:
            return hits
    except Exception:
        pass
    return _fallback(path, "playwright")
