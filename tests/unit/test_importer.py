"""
Unit tests for DataImporter (JSON and CSV file ingestion).
"""

import json
from pathlib import Path
import pytest
from database.init_db import initialize_database
from src.data.provider_repository import SQLiteProviderRepository
from src.data.importer import DataImporter


@pytest.fixture
def repo(tmp_path: Path) -> SQLiteProviderRepository:
    db_file = tmp_path / "test_import.db"
    initialize_database(db_file)
    return SQLiteProviderRepository(db_file)


def test_import_from_json_success(repo: SQLiteProviderRepository, tmp_path: Path):
    """Verify importing valid provider list from JSON."""
    raw_data = [
        {
            "provider_id": "imp_01",
            "name": "Importer Brand A",
            "headquarters_country": "Austria",
            "primary_technologies": ["STRING_INVERTER"],
            "min_capacity_kw": 3.0,
            "max_capacity_kw": 50.0,
            "supported_building_types": ["RESIDENTIAL_INDIVIDUAL"],
            "india_presence_type": "AUTHORIZED_DISTRIBUTOR",
            "pune_service_availability": True,
            "in_country_warehouse": False,
            "certifications": ["IEC 62109"],
            "warranty_terms": {"years": 5},
            "estimated_cost_tier": "MID_RANGE",
            "is_sample_data": False,
            "last_audit_date": "2026-10-01",
            "evidence_records": [
                {
                    "citation_id": "c1",
                    "claim": "Inverter efficiency report",
                    "source_url": "https://example.com/datasheet.pdf",
                    "source_type": "PRODUCT_DATASHEET",
                    "last_verified": "2026-10-01"
                }
            ]
        }
    ]
    json_file = tmp_path / "valid.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(raw_data, f)

    importer = DataImporter(repo)
    summary = importer.import_from_json(json_file)

    assert summary.total_records == 1
    assert summary.imported == 1
    assert summary.failed == 0
    assert repo.count_providers() == 1


def test_import_deduplication(repo: SQLiteProviderRepository, tmp_path: Path):
    """Verify that re-importing the same provider ID updates rather than creating duplicate."""
    raw_data = [
        {
            "provider_id": "imp_dedup",
            "name": "Initial Name",
            "headquarters_country": "Austria",
            "primary_technologies": ["STRING_INVERTER"],
            "min_capacity_kw": 3.0,
            "max_capacity_kw": 50.0,
            "supported_building_types": ["RESIDENTIAL_INDIVIDUAL"],
            "india_presence_type": "AUTHORIZED_DISTRIBUTOR",
            "is_sample_data": False,
            "last_audit_date": "2026-10-01",
            "evidence_records": [
                {
                    "citation_id": "c1",
                    "claim": "Claim",
                    "source_url": "https://example.com/datasheet.pdf",
                    "source_type": "PRODUCT_DATASHEET",
                    "last_verified": "2026-10-01"
                }
            ]
        }
    ]
    json_file = tmp_path / "dedup.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(raw_data, f)

    importer = DataImporter(repo)
    summary1 = importer.import_from_json(json_file)
    assert summary1.imported == 1

    # Modify and re-import
    raw_data[0]["name"] = "Updated Name"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(raw_data, f)

    summary2 = importer.import_from_json(json_file)
    assert summary2.imported == 0
    assert summary2.updated == 1
    assert repo.count_providers() == 1
    assert repo.get_provider_by_id("imp_dedup").name == "Updated Name"


def test_import_handles_malformed_record_gracefully(repo: SQLiteProviderRepository, tmp_path: Path):
    """Verify that a malformed record is reported without aborting valid sibling records."""
    mixed_data = [
        {
            "provider_id": "valid_01",
            "name": "Good Record",
            "headquarters_country": "Germany",
            "primary_technologies": ["STRING_INVERTER"],
            "min_capacity_kw": 2.0,
            "max_capacity_kw": 20.0,
            "supported_building_types": ["COMMERCIAL"],
            "india_presence_type": "DIRECT_SUBSIDIARY",
            "last_audit_date": "2026-10-01",
            "evidence_records": [
                {
                    "citation_id": "c1",
                    "claim": "Valid",
                    "source_url": "https://example.com/doc.pdf",
                    "source_type": "PRODUCT_DATASHEET",
                    "last_verified": "2026-10-01"
                }
            ]
        },
        {
            "provider_id": "bad_02",
            "name": "Bad Record (inverted capacity)",
            "headquarters_country": "Germany",
            "primary_technologies": ["MONO_PERC"],
            "min_capacity_kw": 100.0,
            "max_capacity_kw": 10.0,  # Invalid: min > max
            "supported_building_types": ["COMMERCIAL"],
            "india_presence_type": "DIRECT_SUBSIDIARY",
            "last_audit_date": "2026-10-01",
            "evidence_records": []
        }
    ]
    json_file = tmp_path / "mixed.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(mixed_data, f)

    importer = DataImporter(repo)
    summary = importer.import_from_json(json_file)

    assert summary.total_records == 2
    assert summary.imported == 1
    assert summary.failed == 1
    assert len(summary.errors) == 1
    assert repo.count_providers() == 1
    assert repo.get_provider_by_id("valid_01") is not None


def test_import_nonexistent_file(repo: SQLiteProviderRepository, tmp_path: Path):
    """Verify non-existent file produces error message in summary."""
    importer = DataImporter(repo)
    summary = importer.import_from_json(tmp_path / "nonexistent.json")
    assert summary.total_records == 0
    assert len(summary.errors) == 1
    assert "File not found" in summary.errors[0]
