"""Environment + optional local_paths.json (wizard) merged."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_ROOT = Path(__file__).resolve().parents[2]
_LOCAL_PATHS = _ROOT / "local_paths.json"
_DEFAULT_CSV = "./data/CSV/testcases_vwo_100.csv"


def _normalize_path(value: Optional[str]) -> Optional[str]:
    if not value:
        return value
    v = value.strip().replace("\\", "/")
    if v.startswith(".data/"):
        v = "./data/" + v[6:]
    elif v == ".data":
        v = "./data"
    return v


def _normalize_testcases_path(value: Optional[str]) -> Optional[str]:
    v = _normalize_path(value)
    if not v:
        return v
    p = (_ROOT / v).resolve() if not Path(v).is_absolute() else Path(v)
    if p.is_file():
        return v
    if p.is_dir():
        for name in ("testcases_vwo_100.csv", "testcases.csv"):
            candidate = p / name
            if candidate.is_file():
                try:
                    return "./" + candidate.relative_to(_ROOT).as_posix()
                except ValueError:
                    return str(candidate)
    return v


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    groq_api_key: str
    groq_model: str = "openai/gpt-oss-120b"

    qdrant_path: str = "./qdrant_data"
    qdrant_url: Optional[str] = None

    embed_model: str = "BAAI/bge-m3"
    rerank_model: str = "BAAI/bge-reranker-v2-m3"
    embed_device: str = "cpu"

    selenium_repo_dir: str = Field(
        default="./data/repos/ATB14xSeleniumAdvanceFrameworks",
        validation_alias=AliasChoices("selenium_repo_dir", "SELENIUM_REPO_DIR", "COPILOT_PATH_SELENIUM"),
    )
    playwright_repo_dir: str = Field(
        default="./data/repos/Advance-Playwright-Framework",
        validation_alias=AliasChoices("playwright_repo_dir", "PLAYWRIGHT_REPO_DIR", "COPILOT_PATH_PLAYWRIGHT"),
    )
    testcases_csv: str = Field(
        default="./data/CSV/testcases_vwo_100.csv",
        validation_alias=AliasChoices("testcases_csv", "TESTCASES_CSV", "COPILOT_PATH_VWO_TESTS"),
    )
    pdfs_dir: str = Field(
        default="./data/PDF",
        validation_alias=AliasChoices("pdfs_dir", "PDFS_DIR", "COPILOT_PATH_PDFS"),
    )
    jira_md_dir: str = Field(
        default="./data/MD",
        validation_alias=AliasChoices("jira_md_dir", "JIRA_MD_DIR", "COPILOT_PATH_MARKDOWN"),
    )

    top_k_per_collection: int = 12
    rerank_pool: int = 12
    rerank_top_k: int = 4
    prefetch_limit: int = 60
    history_turns: int = 4


def _merge_local_paths(s: Settings) -> None:
    if not _LOCAL_PATHS.is_file():
        return
    try:
        data: dict[str, Any] = json.loads(_LOCAL_PATHS.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return
    if v := data.get("selenium") or data.get("selenium_repo_dir"):
        s.selenium_repo_dir = _normalize_path(v) or s.selenium_repo_dir
    if v := data.get("playwright") or data.get("playwright_repo_dir"):
        s.playwright_repo_dir = _normalize_path(v) or s.playwright_repo_dir
    if v := data.get("vwo_tests") or data.get("testcases_csv"):
        s.testcases_csv = _normalize_testcases_path(v) or _DEFAULT_CSV
    if v := data.get("pdfs") or data.get("pdfs_dir"):
        s.pdfs_dir = _normalize_path(v) or s.pdfs_dir
    if v := data.get("markdown") or data.get("jira_md_dir"):
        s.jira_md_dir = _normalize_path(v) or s.jira_md_dir


def get_settings() -> Settings:
    s = Settings()
    _merge_local_paths(s)
    return s


def save_local_paths(**kwargs: Optional[str]) -> None:
    data: dict[str, Any] = {}
    if _LOCAL_PATHS.is_file():
        try:
            data = json.loads(_LOCAL_PATHS.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            data = {}
    key_map = {
        "pdfs": "pdfs",
        "markdown": "markdown",
        "selenium": "selenium",
        "playwright": "playwright",
        "vwo_tests": "vwo_tests",
    }
    normalizers = {
        "pdfs": _normalize_path,
        "markdown": _normalize_path,
        "selenium": _normalize_path,
        "playwright": _normalize_path,
        "vwo_tests": _normalize_testcases_path,
    }
    for arg, json_key in key_map.items():
        if arg in kwargs and kwargs[arg] is not None:
            raw = (kwargs[arg] or "").strip() or None
            data[json_key] = normalizers[arg](raw) if raw else None
    _LOCAL_PATHS.write_text(json.dumps(data, indent=2), encoding="utf-8")
