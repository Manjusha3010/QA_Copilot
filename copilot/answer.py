from __future__ import annotations

from typing import List, Literal

from groq import Groq

from copilot.config import Settings

Mode = Literal["docs", "tests"]


def build_system_prompt(mode: Mode) -> str:
    base = (
        "You are a QA co-pilot for app.vwo.com and related automation (Selenium, Playwright). "
        "Use ONLY the provided context for factual claims. "
        "If the context does not contain enough information, say clearly that you do not know "
        "and suggest what source (PDFs, Selenium repo, Playwright repo, tests) might need to be indexed. "
        "When you use facts from context, mention the file path or source type briefly in parentheses where helpful."
    )
    if mode == "tests":
        return (
            base
            + " Prioritize actionable test guidance: locators, flows, assertions, and stability. "
            "Prefer citing concrete steps from the retrieved test or code snippets."
        )
    return (
        base
        + " Prioritize clear explanations of product behavior, requirements, and documentation. "
        "Prefer citing PDFs or written summaries when they are in context."
    )


def run_groq(
    settings: Settings,
    client: Groq,
    query: str,
    context_blocks: List[str],
    mode: Mode,
) -> str:
    system = build_system_prompt(mode)
    ctx = "\n\n---\n\n".join(context_blocks)
    user = f"Context:\n{ctx}\n\nQuestion:\n{query}"
    resp = client.chat.completions.create(
        model=settings.groq_model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.2,
    )
    return (resp.choices[0].message.content or "").strip()
