"""Application configuration loaded from environment variables."""

from __future__ import annotations

from dataclasses import dataclass, field
import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Settings:
    project_root: Path
    database_path: Path
    deepseek_api_key: str = field(repr=False)
    deepseek_api_base: str
    deepseek_model: str


def load_settings(*, require_api_key: bool = True) -> Settings:
    """Load settings without overriding variables already set by the shell."""

    load_dotenv(PROJECT_ROOT / ".env", override=False)

    api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
    if require_api_key and not api_key:
        raise RuntimeError(
            "Missing DEEPSEEK_API_KEY. Copy .env.example to .env and fill in the key."
        )

    # DEEPSEEK_BASE_URL is accepted temporarily for the existing project setup.
    api_base = (
        os.getenv("DEEPSEEK_API_BASE")
        or os.getenv("DEEPSEEK_BASE_URL")
        or "https://api.deepseek.com"
    ).rstrip("/")
    model = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-pro").strip()

    configured_db_path = Path(
        os.getenv("FITNESS_DB_PATH", "app/database/fitness.db")
    )
    if not configured_db_path.is_absolute():
        configured_db_path = PROJECT_ROOT / configured_db_path

    return Settings(
        project_root=PROJECT_ROOT,
        database_path=configured_db_path.resolve(),
        deepseek_api_key=api_key,
        deepseek_api_base=api_base,
        deepseek_model=model,
    )
