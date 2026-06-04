"""System / user prompts for rewrite, answer, citations."""

from __future__ import annotations

from backend.lib.settings import Settings

ANSWER_SYSTEM = """You are a QA copilot. Answer using ONLY the provided <doc> blocks.
Use inline numeric citations like [1], [2] that refer to the doc id attribute.
If context is insufficient, say you do not know and which collection might need more data.
Be concise and factual."""


def format_docs_for_prompt(chunks: list[dict]) -> str:
    parts = []
    for i, ch in enumerate(chunks, start=1):
        pl = ch.get("payload") or {}
        src = pl.get("source_path") or pl.get("path") or ch.get("collection", "")
        meta = []
        if pl.get("tc_id"):
            meta.append(f'tc_id="{pl["tc_id"]}"')
        if pl.get("jira_id"):
            meta.append(f'jira_id="{pl["jira_id"]}"')
        if pl.get("page") is not None:
            meta.append(f'page="{pl["page"]}"')
        if pl.get("start_line") is not None:
            meta.append(f'line="{pl["start_line"]}-{pl.get("end_line", "")}"')
        attr = " ".join([f'id="{i}"', f'source="{src}"'] + meta)
        parts.append(f"<doc {attr}>\n{ch.get('text', '')}\n</doc>")
    return "\n\n".join(parts)


REWRITE_SYSTEM = """Rewrite the user's latest message as a standalone search question.
Use conversation history only if needed for pronouns. Output ONLY the rewritten question, one line."""


def rewrite_query(
    groq,
    settings: Settings,
    history: list[dict],
    latest: str,
) -> str:
    if not history:
        return latest
    lines = []
    for m in history[-settings.history_turns * 2 :]:
        role = m.get("role", "user")
        content = m.get("content", "")
        lines.append(f"{role}: {content}")
    lines.append(f"user: {latest}")
    blob = "\n".join(lines)
    resp = groq.chat.completions.create(
        model=settings.groq_model,
        messages=[
            {"role": "system", "content": REWRITE_SYSTEM},
            {"role": "user", "content": blob},
        ],
        temperature=0,
        max_tokens=256,
    )
    out = (resp.choices[0].message.content or "").strip().split("\n")[0]
    return out or latest
