"""Groq LLM router: pick 1–2 collections per query."""

from __future__ import annotations

import json
import re
from typing import List, Optional

from groq import Groq

from backend.lib.collections import ALL_COLLECTIONS
from backend.lib.settings import Settings

ROUTER_SYSTEM = """You are a routing classifier for a QA copilot over five knowledge bases:
- selenium_code: Selenium Java/TestNG automation code
- playwright_code: Playwright TypeScript/JavaScript tests and fixtures
- vwo_testcases: CSV rows of VWO test cases (ids, steps, modules, priority)
- vwo_docs: product PDFs / PRDs / specifications
- vwo_bugs: JIRA bug exports as Markdown files

Given a user question, reply with ONLY a JSON array of 1 or 2 strings, each string EXACTLY one of:
["selenium_code","playwright_code","vwo_testcases","vwo_docs","vwo_bugs"]

Examples:
- "How does BasePage wait work?" -> ["selenium_code"]
- "List P0 admin test cases" -> ["vwo_testcases"]
- "What does the PRD say about login?" -> ["vwo_docs"]
- "Open bugs for login" -> ["vwo_bugs"]
- "Playwright fixture auth" -> ["playwright_code"]
No markdown fences. No extra text."""


def route_collections_with_meta(
    settings: Settings,
    groq: Groq,
    question: str,
    override: Optional[List[str]],
) -> tuple[List[str], str, bool]:
    """Returns (collections, raw_router_output_or_override_json, used_fallback_all_collections)."""
    if override:
        cols = [c for c in override if c in ALL_COLLECTIONS]
        note = json.dumps({"user_source_override": override, "effective": cols})
        return cols, note, False
    resp = groq.chat.completions.create(
        model=settings.groq_model,
        messages=[
            {"role": "system", "content": ROUTER_SYSTEM},
            {"role": "user", "content": question},
        ],
        temperature=0,
        max_tokens=128,
    )
    raw = (resp.choices[0].message.content or "").strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", raw)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        arr = json.loads(cleaned)
    except json.JSONDecodeError:
        return list(ALL_COLLECTIONS), raw, True
    if not isinstance(arr, list):
        return list(ALL_COLLECTIONS), raw, True
    picked = [x for x in arr if x in ALL_COLLECTIONS]
    if not picked:
        return list(ALL_COLLECTIONS), raw, True
    return picked[:2], raw, False


def route_collections(
    settings: Settings,
    groq: Groq,
    question: str,
    override: Optional[List[str]],
) -> List[str]:
    cols, _, _ = route_collections_with_meta(settings, groq, question, override)
    return cols
