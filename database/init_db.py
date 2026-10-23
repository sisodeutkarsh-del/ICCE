"""
Database initialization module for the International Solar Technology Partner Matching Agent.
Creates tables, indexes, and constraints in the local SQLite database.
"""

import sqlite3
import sys
from pathlib import Path

# Add project root to sys.path for standalone script execution
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config.settings import get_settings
from src.utils.logger import logger


SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS providers (
    provider_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    headquarters_country TEXT NOT NULL,
    primary_technologies TEXT NOT NULL,
    min_capacity_kw REAL NOT NULL,
    max_capacity_kw REAL NOT NULL,
    supported_building_types TEXT NOT NULL,
    india_presence_type TEXT NOT NULL,
    pune_service_availability INTEGER NOT NULL DEFAULT 0,
    in_country_warehouse INTEGER NOT NULL DEFAULT 0,
    certifications TEXT NOT NULL,
    warranty_terms TEXT NOT NULL,
    estimated_cost_tier TEXT NOT NULL,
    is_sample_data INTEGER NOT NULL DEFAULT 0,
    last_audit_date TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_providers_is_sample ON providers(is_sample_data);
CREATE INDEX IF NOT EXISTS idx_providers_capacity ON providers(min_capacity_kw, max_capacity_kw);

CREATE TABLE IF NOT EXISTS evidence (
    citation_id TEXT PRIMARY KEY,
    provider_id TEXT NOT NULL,
    claim TEXT NOT NULL,
    source_url TEXT NOT NULL,
    source_type TEXT NOT NULL,
    last_verified TEXT NOT NULL,
    verification_note TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (provider_id) REFERENCES providers(provider_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_evidence_provider ON evidence(provider_id);

CREATE TABLE IF NOT EXISTS project_history (
    project_id TEXT PRIMARY KEY,
    project_name TEXT NOT NULL,
    pune_locality TEXT NOT NULL,
    building_type TEXT NOT NULL,
    target_capacity_kw REAL NOT NULL,
    budget_inr REAL,
    roof_type TEXT NOT NULL,
    grid_coupling TEXT NOT NULL,
    service_requirement TEXT NOT NULL,
    raw_profile_json TEXT NOT NULL,
    match_results_json TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_project_history_created ON project_history(created_at);
"""


def get_db_connection(db_path: Path) -> sqlite3.Connection:
    """Returns an open SQLite connection with foreign keys enabled and row factory set."""
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database(db_path: Path) -> None:
    """Creates the SQLite database and executes the schema DDL."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info("Initializing SQLite database at: %s", db_path)
    
    with get_db_connection(db_path) as conn:
        conn.executescript(SCHEMA_SQL)
        conn.commit()
        
    logger.info("Database schema initialized successfully.")


if __name__ == "__main__":
    settings = get_settings()
    initialize_database(settings.absolute_db_path)
