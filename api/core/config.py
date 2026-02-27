"""
MindWall — Application Configuration
Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)

Pydantic-settings based configuration loaded from environment variables.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # API
    api_secret_key: str = "changeme"
    database_url: str = "sqlite+aiosqlite:////app/data/db/mindwall.db"
    log_level: str = "INFO"
    workers: int = 4

    # Ollama LLM
    ollama_base_url: str = "http://ollama:11434"
    ollama_model: str = "mindwall-llama3.1-8b"
    ollama_timeout_seconds: int = 30

    # Alert Thresholds
    alert_medium_threshold: float = 35.0
    alert_high_threshold: float = 60.0
    alert_critical_threshold: float = 80.0


@lru_cache()
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    return Settings()
