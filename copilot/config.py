import json
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

_LOCAL_PATHS_FILE = Path(__file__).resolve().parent.parent / "local_paths.json"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    groq_api_key: str
    groq_model: str = "llama-3.3-70b-versatile"

    qdrant_path: str = "./qdrant_storage"
    qdrant_url: Optional[str] = None

    embed_model: str = "BAAI/bge-m3"
    reranker_model: str = "BAAI/bge-reranker-v2-m3"

    path_pdfs: Optional[str] = None
    path_markdown: Optional[str] = "./data/MD"
    path_selenium: Optional[str] = None
    path_playwright: Optional[str] = None
    path_vwo_tests: Optional[str] = None

    retrieve_k_per_collection: int = 8
    rerank_top_n: int = 48
    context_chunks: int = 12


def _merge_local_paths(settings: Settings) -> None:
    if not _LOCAL_PATHS_FILE.is_file():
        return
    try:
        data = json.loads(_LOCAL_PATHS_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return
    if p := data.get("pdfs"):
        settings.path_pdfs = p
    if "markdown" in data:
        settings.path_markdown = data.get("markdown") or None
    if p := data.get("selenium"):
        settings.path_selenium = p
    if p := data.get("playwright"):
        settings.path_playwright = p
    if p := data.get("vwo_tests"):
        settings.path_vwo_tests = p


def save_local_paths(
    pdfs: Optional[str] = None,
    markdown: Optional[str] = None,
    selenium: Optional[str] = None,
    playwright: Optional[str] = None,
    vwo_tests: Optional[str] = None,
) -> None:
    data: dict = {}
    if _LOCAL_PATHS_FILE.is_file():
        try:
            data = json.loads(_LOCAL_PATHS_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            data = {}
    if pdfs is not None:
        data["pdfs"] = (pdfs or "").strip() or None
    if markdown is not None:
        data["markdown"] = (markdown or "").strip() or None
    if selenium is not None:
        data["selenium"] = (selenium or "").strip() or None
    if playwright is not None:
        data["playwright"] = (playwright or "").strip() or None
    if vwo_tests is not None:
        data["vwo_tests"] = (vwo_tests or "").strip() or None
    _LOCAL_PATHS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def get_settings() -> Settings:
    s = Settings()
    _merge_local_paths(s)
    return s
