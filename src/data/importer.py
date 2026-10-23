"""
Data ingestion module for importing solar technology provider records from JSON or CSV files.
Enforces Pydantic schema validation, records import statistics, and reports validation errors.
"""

import csv
import json
from pathlib import Path
from typing import Any, Dict, List
from pydantic import BaseModel, Field, ValidationError
from src.domain.models import ProviderRecord
from src.data.provider_repository import SQLiteProviderRepository
from src.utils.logger import logger


class ImportSummary(BaseModel):
    """Execution summary of a data import operation."""
    total_records: int = 0
    imported: int = 0
    updated: int = 0
    failed: int = 0
    errors: List[str] = Field(default_factory=list)


class DataImporter:
    """Imports and validates provider records into SQLite repository."""

    def __init__(self, repository: SQLiteProviderRepository):
        self.repository = repository

    def import_from_json(self, file_path: Path) -> ImportSummary:
        """Reads, validates, and upserts provider records from a JSON file."""
        summary = ImportSummary()
        if not file_path.exists():
            summary.errors.append(f"File not found: {file_path}")
            return summary

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            summary.errors.append(f"Failed to parse JSON file {file_path}: {str(e)}")
            return summary

        if not isinstance(data, list):
            summary.errors.append(f"JSON root must be an array of provider objects in {file_path}")
            return summary

        summary.total_records = len(data)
        for idx, item in enumerate(data):
            try:
                record = ProviderRecord.model_validate(item)
                existing = self.repository.get_provider_by_id(record.provider_id)
                self.repository.upsert_provider(record)
                if existing:
                    summary.updated += 1
                else:
                    summary.imported += 1
            except ValidationError as ve:
                summary.failed += 1
                err_msg = f"Record #{idx} ({item.get('provider_id', 'unknown_id')}) validation failed: {ve.errors()}"
                summary.errors.append(err_msg)
                logger.warning(err_msg)
            except Exception as e:
                summary.failed += 1
                err_msg = f"Record #{idx} ({item.get('provider_id', 'unknown_id')}) import error: {str(e)}"
                summary.errors.append(err_msg)
                logger.error(err_msg)

        logger.info(
            "Import completed for %s: %d imported, %d updated, %d failed out of %d total",
            file_path.name, summary.imported, summary.updated, summary.failed, summary.total_records
        )
        return summary

    def import_from_csv(self, file_path: Path) -> ImportSummary:
        """Reads, deserializes, and validates provider records from a CSV file."""
        summary = ImportSummary()
        if not file_path.exists():
            summary.errors.append(f"File not found: {file_path}")
            return summary

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
        except Exception as e:
            summary.errors.append(f"Failed to read CSV file {file_path}: {str(e)}")
            return summary

        summary.total_records = len(rows)
        for idx, row in enumerate(rows):
            try:
                # Parse JSON string fields inside CSV
                deserialized: Dict[str, Any] = {
                    "provider_id": row["provider_id"],
                    "name": row["name"],
                    "headquarters_country": row["headquarters_country"],
                    "primary_technologies": [t.strip() for t in row["primary_technologies"].split(",")],
                    "min_capacity_kw": float(row["min_capacity_kw"]),
                    "max_capacity_kw": float(row["max_capacity_kw"]),
                    "supported_building_types": [b.strip() for b in row["supported_building_types"].split(",")],
                    "india_presence_type": row["india_presence_type"],
                    "pune_service_availability": row["pune_service_availability"].strip().lower() in ["true", "1", "yes"],
                    "in_country_warehouse": row["in_country_warehouse"].strip().lower() in ["true", "1", "yes"],
                    "certifications": [c.strip() for c in row["certifications"].split(",") if c.strip()],
                    "warranty_terms": json.loads(row["warranty_terms"]) if row.get("warranty_terms") else {},
                    "estimated_cost_tier": row.get("estimated_cost_tier", "MID_RANGE"),
                    "is_sample_data": row.get("is_sample_data", "false").strip().lower() in ["true", "1", "yes"],
                    "last_audit_date": row["last_audit_date"],
                    "evidence_records": json.loads(row["evidence_records"]),
                }
                record = ProviderRecord.model_validate(deserialized)
                existing = self.repository.get_provider_by_id(record.provider_id)
                self.repository.upsert_provider(record)
                if existing:
                    summary.updated += 1
                else:
                    summary.imported += 1
            except ValidationError as ve:
                summary.failed += 1
                err_msg = f"CSV row #{idx+1} ({row.get('provider_id', 'unknown')}) validation failed: {ve.errors()}"
                summary.errors.append(err_msg)
            except Exception as e:
                summary.failed += 1
                err_msg = f"CSV row #{idx+1} ({row.get('provider_id', 'unknown')}) error: {str(e)}"
                summary.errors.append(err_msg)

        logger.info("CSV import completed: %d imported, %d updated, %d failed", summary.imported, summary.updated, summary.failed)
        return summary
