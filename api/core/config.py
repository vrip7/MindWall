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

    # Dashboard Login
    dashboard_username: str = "admin"
    dashboard_password: str = "MindWall@2026"

    # Ollama LLM
    ollama_base_url: str = "http://ollama:11434"
    ollama_model: str = "qwen3:8b"
    ollama_timeout_seconds: int = 30

    # Alert Thresholds
    alert_medium_threshold: float = 35.0
    alert_high_threshold: float = 60.0
    alert_critical_threshold: float = 80.0

    # Pipeline Weights
    prefilter_score_boost: float = 15.0
    behavioral_weight: float = 0.6
    llm_weight: float = 0.4

    # Proxy ports (for connection info display)
    proxy_imap_port: int = 1143
    proxy_smtp_port: int = 1025


@lru_cache()
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    return Settings()
