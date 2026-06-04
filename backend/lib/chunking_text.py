"""Row-aware chunks for VWO testcase CSV (Chapter 9 schema)."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Dict, List, Tuple


def chunk_testcases_csv(path: Path) -> List[Tuple[str, Dict[str, Any]]]:
    out: List[Tuple[str, Dict[str, Any]]] = []
    if not path.is_file():
        return out
    with path.open(encoding="utf-8", errors="replace", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        for row in reader:
            parts = []
            for k in fieldnames:
                v = (row.get(k) or "").strip()
                if v:
                    parts.append(f"{k}: {v}")
            text = "\n".join(parts)
            if not text:
                continue
            meta = {
                "source_type": "testcase_csv",
                "path": str(path),
                "tc_id": (row.get("id") or row.get("tc_id") or "").strip(),
                "jira_id": (row.get("jira_id") or "").strip(),
                "module": (row.get("module") or "").strip(),
                "priority": (row.get("priority") or "").strip(),
                "severity": (row.get("severity") or "").strip(),
                "labels": (row.get("labels") or "").strip(),
                "sprint": (row.get("sprint") or "").strip(),
                "status": (row.get("status") or "").strip(),
                "owner": (row.get("owner") or "").strip(),
                "test_type": (row.get("test_type") or "").strip(),
            }
            out.append((text, meta))
    return out
