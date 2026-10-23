"""
Configuration module for the International Solar Technology Partner Matching Agent.
Uses Pydantic BaseSettings to validate environment variables and provide safe defaults.
"""

from pathlib import Path
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Application configuration settings loaded from environment or .env file."""

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Application Environment
    app_env: str = Field(default="development", description="Runtime environment (development, testing, production)")
    log_level: str = Field(default="INFO", description="Logging verbosity (DEBUG, INFO, WARNING, ERROR)")

    # Model API Keys (Empty by default; fallback to deterministic matching if absent)
    openrouter_api_key: Optional[str] = Field(default=None, description="OpenRouter API key")
    huggingface_api_key: Optional[str] = Field(default=None, description="Hugging Face API key")
    gemini_api_key: Optional[str] = Field(default=None, description="Google Gemini API key")

    # Model IDs
    openrouter_model: str = Field(default="meta-llama/llama-3.1-8b-instruct:free", description="Default OpenRouter model")
    huggingface_model: str = Field(default="mistralai/Mistral-7B-Instruct-v0.3", description="Default HuggingFace model")
    gemini_model: str = Field(default="gemini-1.5-flash", description="Default Gemini model")

    # Gateway Execution Tuning
    llm_timeout_seconds: int = Field(default=15, description="Timeout per LLM request in seconds")
    llm_max_retries: int = Field(default=2, description="Maximum retry attempts on retryable errors")
    llm_backoff_base_seconds: float = Field(default=1.0, description="Base exponential backoff factor in seconds")

    # Storage Paths
    database_path: str = Field(default="database/solar_agent.db", description="Relative or absolute path to SQLite DB")
    verified_data_path: str = Field(default="data/verified_providers.json", description="Path to verified provider catalog")
    sample_fixtures_path: str = Field(default="data/sample_fixtures.json", description="Path to sample fixtures")

    @property
    def absolute_db_path(self) -> Path:
        """Returns the absolute path to the SQLite database file."""
        p = Path(self.database_path)
        return p if p.is_absolute() else BASE_DIR / p

    @property
    def absolute_verified_data_path(self) -> Path:
        p = Path(self.verified_data_path)
        return p if p.is_absolute() else BASE_DIR / p

    @property
    def absolute_sample_fixtures_path(self) -> Path:
        p = Path(self.sample_fixtures_path)
        return p if p.is_absolute() else BASE_DIR / p

    def masked_key(self, key_name: str) -> str:
        """Returns a sanitized masked representation of a sensitive key for UI/logging display."""
        val = getattr(self, key_name, None)
        if not val or len(val) < 8:
            return "Not Configured" if not val else "***"
        return f"{val[:6]}...{val[-4:]}"


def get_settings() -> Settings:
    """Factory function to instantiate settings singleton."""
    return Settings()
