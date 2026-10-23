"""
Unit tests for Phase 1: Foundation, Configuration, and Database Setup.
"""

import json
import sqlite3
from pathlib import Path
import pytest
from config.settings import Settings, get_settings
from database.init_db import initialize_database, get_db_connection, SCHEMA_SQL
from src.utils.logger import SanitizedFormatter


def test_settings_load_defaults():
    """Verify settings instantiate with valid default parameters."""
    settings = get_settings()
    assert settings.app_env in ["development", "testing", "production"]
    assert settings.llm_timeout_seconds > 0
    assert settings.llm_max_retries >= 1
    assert "solar_agent.db" in str(settings.absolute_db_path)


def test_masked_key_security():
    """Verify sensitive keys are masked and raw secrets are never exposed."""
    s = Settings(
        openrouter_api_key="mock-test-key-abcdef1234567890abcdef1234567890",
        gemini_api_key=None
    )
    masked = s.masked_key("openrouter_api_key")
    assert "mock-t" in masked
    assert "7890" in masked
    assert "abcdef1234567890" not in masked
    assert s.masked_key("gemini_api_key") == "Not Configured"


def test_logger_redaction():
    """Verify the logger formatter redacts known secret patterns."""
    formatter = SanitizedFormatter("%(message)s")
    
    class DummyRecord:
        def __init__(self, msg):
            self.msg = msg
            self.args = None
            self.exc_info = None
            self.exc_text = None
            self.stack_info = None

        def getMessage(self):
            return self.msg

    rec = DummyRecord("Calling service with key mock-test-key-0123456789abcdef0123456789abcdef now")
    formatted = formatter.format(rec)
    assert "mock-test-key-01234567...[REDACTED]" in formatted
    assert "0123456789abcdef0123456789abcdef" not in formatted


def test_database_initialization(tmp_path: Path):
    """Verify database schema creates providers, evidence, and project_history tables."""
    test_db = tmp_path / "test_solar.db"
    initialize_database(test_db)
    assert test_db.exists()

    with get_db_connection(test_db) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}
        assert "providers" in tables
        assert "evidence" in tables
        assert "project_history" in tables

        # Verify foreign keys are enabled via connection factory
        cursor.execute("PRAGMA foreign_keys")
        fk_status = cursor.fetchone()[0]
        assert fk_status == 1


def test_sample_fixtures_schema():
    """Verify deterministic sample fixtures are valid JSON and labeled as sample data."""
    settings = get_settings()
    fixtures_path = settings.absolute_sample_fixtures_path
    assert fixtures_path.exists(), f"Sample fixtures file not found at {fixtures_path}"

    with open(fixtures_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert isinstance(data, list)
    assert len(data) >= 3
    for record in data:
        assert record["is_sample_data"] is True
        assert "provider_id" in record
        assert "min_capacity_kw" in record
        assert "max_capacity_kw" in record
        assert record["min_capacity_kw"] <= record["max_capacity_kw"]
        assert len(record["evidence_records"]) >= 1
