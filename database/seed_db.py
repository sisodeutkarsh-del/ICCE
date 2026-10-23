"""
Database seeding script.
Imports verified provider records and sample fixtures into SQLite database.
"""

import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config.settings import get_settings
from database.init_db import initialize_database
from src.data.provider_repository import SQLiteProviderRepository
from src.data.importer import DataImporter
from src.utils.logger import logger


def seed_database():
    """Initializes schema and ingests verified catalog + sample fixtures."""
    settings = get_settings()
    initialize_database(settings.absolute_db_path)

    repo = SQLiteProviderRepository(settings.absolute_db_path)
    importer = DataImporter(repo)

    logger.info("Importing verified providers from: %s", settings.absolute_verified_data_path)
    v_summary = importer.import_from_json(settings.absolute_verified_data_path)
    logger.info("Verified providers import: %s", v_summary)

    logger.info("Importing sample fixtures from: %s", settings.absolute_sample_fixtures_path)
    s_summary = importer.import_from_json(settings.absolute_sample_fixtures_path)
    logger.info("Sample fixtures import: %s", s_summary)

    total = repo.count_providers(include_sample=True)
    verified = repo.count_providers(include_sample=False)
    logger.info("Database seeding complete. Total providers: %d (Verified: %d, Sample: %d)", total, verified, total - verified)


if __name__ == "__main__":
    seed_database()
