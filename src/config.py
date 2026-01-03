from __future__ import annotations
"""Configuration centralisée pour l'application."""

from pathlib import Path
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application configuration."""

    # Paths
    base_path: Path = Path(__file__).parent.parent
    raw_data_path: Path = base_path / "data" / "raw"
    db_path: Path = base_path / "data" / "db"

    # Database
    database_url: str = f"sqlite:///{db_path}/financials.db"

    # Google Drive
    gdrive_credentials_path: Path = base_path / "credentials.json"
    gdrive_token_path: Path = base_path / "token.json"
    gdrive_root_folder_id: str = ""

    # Google Drive API scopes (read + write for uploading results)
    gdrive_scopes: list[str] = ["https://www.googleapis.com/auth/drive"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Allow extra env vars (API keys, etc.)


@lru_cache
def get_settings() -> Settings:
    """Retourne l'instance de configuration (singleton)."""
    return Settings()
