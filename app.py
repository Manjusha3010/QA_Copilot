"""QA Copilot entrypoint. Requires Python 3.11–3.13 (not 3.14+)."""

from __future__ import annotations

import sys
from pathlib import Path

_MIN = (3, 11)
_MAX = (3, 13)
_ROOT = Path(__file__).resolve().parent


def _check_python() -> None:
    v = sys.version_info[:3]
    if v < _MIN or v > _MAX:
        rel = ".venv\\Scripts\\python.exe" if sys.platform == "win32" else ".venv/bin/python"
        print(
            f"ERROR: QA Copilot needs Python 3.11–3.13; you are on {sys.version.split()[0]}.\n"
            "Python 3.14 breaks qdrant-client/protobuf (Metaclasses error).\n\n"
            "Use the project venv instead:\n"
            "  .\\.venv\\Scripts\\activate\n"
            "  python app.py\n\n"
            "Or in one line:\n"
            f"  .\\{rel} app.py\n"
            "Or:  .\\start.ps1\n",
            file=sys.stderr,
        )
        sys.exit(1)


_check_python()

from backend.main import app
from backend.run_config import api_port

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="0.0.0.0", port=api_port(), reload=True)
