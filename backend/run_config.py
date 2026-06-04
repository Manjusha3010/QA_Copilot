"""Process bind port for uvicorn (avoid clashes with other local apps on 8000 / 8500)."""

from __future__ import annotations

import os

# Default API port for QA Copilot only; override without code edits:
#   set QACOPILOT_API_PORT=9100
# Vite dev proxy: set VITE_API_PROXY=http://127.0.0.1:<same> in frontend/.env
DEFAULT_API_PORT = 8843


def api_port() -> int:
    raw = os.environ.get("QACOPILOT_API_PORT", str(DEFAULT_API_PORT)).strip()
    try:
        p = int(raw)
    except ValueError:
        return DEFAULT_API_PORT
    if 1 <= p <= 65535:
        return p
    return DEFAULT_API_PORT
