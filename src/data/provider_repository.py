"""
SQLite repository implementation for ProviderRecord and Evidence entities.
Encapsulates all database queries, JSON serialization, and object reconstruction.
"""

import json
import sqlite3
from pathlib import Path
from typing import List, Optional
from database.init_db import get_db_connection
from src.domain.models import (
    ProviderRecord,
    EvidenceCitation,
    TechType,
    BuildingType,
    IndiaPresence,
    CostTier,
    SourceType,
)
from src.utils.logger import logger


class SQLiteProviderRepository:
    """Manages persistent storage and querying of solar technology providers."""

    def __init__(self, db_path: Path):
        self.db_path = db_path

    def _row_to_provider(self, conn: sqlite3.Connection, row: sqlite3.Row) -> ProviderRecord:
        """Hydrates a ProviderRecord along with its child Evidence records."""
        provider_id = row["provider_id"]
        
        # Query associated evidence citations
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT citation_id, claim, source_url, source_type, last_verified, verification_note
            FROM evidence
            WHERE provider_id = ?
            ORDER BY last_verified DESC
            """,
            (provider_id,)
        )
        evidence_rows = cursor.fetchall()
        
        evidence_list = [
            EvidenceCitation(
                citation_id=ev["citation_id"],
                claim=ev["claim"],
                source_url=ev["source_url"],
                source_type=SourceType(ev["source_type"]),
                last_verified=ev["last_verified"],
                verification_note=ev["verification_note"],
            )
            for ev in evidence_rows
        ]

        return ProviderRecord(
            provider_id=row["provider_id"],
            name=row["name"],
            headquarters_country=row["headquarters_country"],
            primary_technologies=[TechType(t) for t in json.loads(row["primary_technologies"])],
            min_capacity_kw=float(row["min_capacity_kw"]),
            max_capacity_kw=float(row["max_capacity_kw"]),
            supported_building_types=[BuildingType(b) for b in json.loads(row["supported_building_types"])],
            india_presence_type=IndiaPresence(row["india_presence_type"]),
            pune_service_availability=bool(row["pune_service_availability"]),
            in_country_warehouse=bool(row["in_country_warehouse"]),
            certifications=json.loads(row["certifications"]),
            warranty_terms=json.loads(row["warranty_terms"]),
            estimated_cost_tier=CostTier(row["estimated_cost_tier"]),
            is_sample_data=bool(row["is_sample_data"]),
            last_audit_date=row["last_audit_date"],
            evidence_records=evidence_list,
        )

    def upsert_provider(self, provider: ProviderRecord) -> None:
        """Inserts or updates a provider and its evidence citations in an atomic transaction."""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                """
                INSERT INTO providers (
                    provider_id, name, headquarters_country, primary_technologies,
                    min_capacity_kw, max_capacity_kw, supported_building_types,
                    india_presence_type, pune_service_availability, in_country_warehouse,
                    certifications, warranty_terms, estimated_cost_tier, is_sample_data,
                    last_audit_date, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                ON CONFLICT(provider_id) DO UPDATE SET
                    name = excluded.name,
                    headquarters_country = excluded.headquarters_country,
                    primary_technologies = excluded.primary_technologies,
                    min_capacity_kw = excluded.min_capacity_kw,
                    max_capacity_kw = excluded.max_capacity_kw,
                    supported_building_types = excluded.supported_building_types,
                    india_presence_type = excluded.india_presence_type,
                    pune_service_availability = excluded.pune_service_availability,
                    in_country_warehouse = excluded.in_country_warehouse,
                    certifications = excluded.certifications,
                    warranty_terms = excluded.warranty_terms,
                    estimated_cost_tier = excluded.estimated_cost_tier,
                    is_sample_data = excluded.is_sample_data,
                    last_audit_date = excluded.last_audit_date,
                    updated_at = datetime('now')
                """,
                (
                    provider.provider_id,
                    provider.name,
                    provider.headquarters_country,
                    json.dumps([t.value for t in provider.primary_technologies]),
                    provider.min_capacity_kw,
                    provider.max_capacity_kw,
                    json.dumps([b.value for b in provider.supported_building_types]),
                    provider.india_presence_type.value,
                    1 if provider.pune_service_availability else 0,
                    1 if provider.in_country_warehouse else 0,
                    json.dumps(provider.certifications),
                    json.dumps(provider.warranty_terms),
                    provider.estimated_cost_tier.value,
                    1 if provider.is_sample_data else 0,
                    str(provider.last_audit_date),
                )
            )

            # Refresh evidence records: remove existing and re-insert
            cursor.execute("DELETE FROM evidence WHERE provider_id = ?", (provider.provider_id,))
            for ev in provider.evidence_records:
                cursor.execute(
                    """
                    INSERT INTO evidence (
                        citation_id, provider_id, claim, source_url, source_type,
                        last_verified, verification_note
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        ev.citation_id,
                        provider.provider_id,
                        ev.claim,
                        str(ev.source_url),
                        ev.source_type.value,
                        str(ev.last_verified),
                        ev.verification_note,
                    )
                )
            
            conn.commit()
            logger.debug("Successfully upserted provider: %s (%s)", provider.name, provider.provider_id)

    def get_provider_by_id(self, provider_id: str) -> Optional[ProviderRecord]:
        """Retrieves a single provider by ID or None if not found."""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM providers WHERE provider_id = ?", (provider_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_provider(conn, row)

    def list_providers(
        self,
        include_sample: bool = True,
        verified_only: bool = False,
        min_cap: Optional[float] = None,
        max_cap: Optional[float] = None,
    ) -> List[ProviderRecord]:
        """Queries providers with optional filters."""
        query = "SELECT * FROM providers WHERE 1=1"
        params = []

        if verified_only:
            query += " AND is_sample_data = 0"
        elif not include_sample:
            query += " AND is_sample_data = 0"

        if min_cap is not None:
            query += " AND max_capacity_kw >= ?"
            params.append(min_cap)

        if max_cap is not None:
            query += " AND min_capacity_kw <= ?"
            params.append(max_cap)

        query += " ORDER BY name ASC"

        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [self._row_to_provider(conn, r) for r in rows]

    def delete_provider(self, provider_id: str) -> bool:
        """Deletes a provider and its cascade evidence records."""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM providers WHERE provider_id = ?", (provider_id,))
            conn.commit()
            return cursor.rowcount > 0

    def count_providers(self, include_sample: bool = True) -> int:
        """Returns total provider count."""
        query = "SELECT COUNT(*) FROM providers" if include_sample else "SELECT COUNT(*) FROM providers WHERE is_sample_data = 0"
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            return cursor.fetchone()[0]
