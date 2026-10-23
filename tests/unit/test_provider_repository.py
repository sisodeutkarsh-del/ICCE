"""
Unit tests for SQLiteProviderRepository CRUD operations and filtering.
"""

from datetime import date
from pathlib import Path
import pytest
from database.init_db import initialize_database
from src.data.provider_repository import SQLiteProviderRepository
from src.domain.models import (
    ProviderRecord,
    EvidenceCitation,
    BuildingType,
    TechType,
    IndiaPresence,
    CostTier,
    SourceType,
)


@pytest.fixture
def repo(tmp_path: Path) -> SQLiteProviderRepository:
    db_file = tmp_path / "test_repo.db"
    initialize_database(db_file)
    return SQLiteProviderRepository(db_file)


def create_dummy_provider(provider_id: str, is_sample: bool = False, min_kw: float = 5.0, max_kw: float = 100.0) -> ProviderRecord:
    return ProviderRecord(
        provider_id=provider_id,
        name=f"Brand {provider_id}",
        headquarters_country="Germany",
        primary_technologies=[TechType.STRING_INVERTER],
        min_capacity_kw=min_kw,
        max_capacity_kw=max_kw,
        supported_building_types=[BuildingType.COMMERCIAL, BuildingType.HOUSING_SOCIETY],
        india_presence_type=IndiaPresence.DIRECT_SUBSIDIARY,
        pune_service_availability=True,
        in_country_warehouse=True,
        certifications=["IEC 62109"],
        warranty_terms={"years": 10},
        estimated_cost_tier=CostTier.PREMIUM_TIER1,
        is_sample_data=is_sample,
        last_audit_date=date(2026, 10, 1),
        evidence_records=[
            EvidenceCitation(
                citation_id=f"ev_{provider_id}_1",
                claim="Datasheet claim verification",
                source_url="https://example.com/datasheet.pdf",
                source_type=SourceType.PRODUCT_DATASHEET,
                last_verified=date(2026, 10, 1)
            )
        ]
    )


def test_upsert_and_get_provider(repo: SQLiteProviderRepository):
    """Verify inserting and retrieving a provider with child evidence."""
    p = create_dummy_provider("prv_01", is_sample=False)
    repo.upsert_provider(p)

    fetched = repo.get_provider_by_id("prv_01")
    assert fetched is not None
    assert fetched.name == "Brand prv_01"
    assert len(fetched.evidence_records) == 1
    assert fetched.evidence_records[0].citation_id == "ev_prv_01_1"


def test_upsert_updates_existing_provider(repo: SQLiteProviderRepository):
    """Verify upserting with existing ID updates fields without duplicate keys."""
    p = create_dummy_provider("prv_01", min_kw=10.0, max_kw=100.0)
    repo.upsert_provider(p)

    # Update capacity and name
    updated_p = create_dummy_provider("prv_01", min_kw=15.0, max_kw=150.0)
    updated_p.name = "Brand prv_01 Renamed"
    repo.upsert_provider(updated_p)

    fetched = repo.get_provider_by_id("prv_01")
    assert fetched is not None
    assert fetched.name == "Brand prv_01 Renamed"
    assert fetched.min_capacity_kw == 15.0
    assert fetched.max_capacity_kw == 150.0
    assert repo.count_providers() == 1


def test_list_providers_filter_sample_data(repo: SQLiteProviderRepository):
    """Verify filtering between verified and sample data."""
    p_real = create_dummy_provider("real_01", is_sample=False)
    p_sample = create_dummy_provider("sample_01", is_sample=True)
    repo.upsert_provider(p_real)
    repo.upsert_provider(p_sample)

    assert repo.count_providers(include_sample=True) == 2
    assert repo.count_providers(include_sample=False) == 1

    verified_only = repo.list_providers(verified_only=True)
    assert len(verified_only) == 1
    assert verified_only[0].provider_id == "real_01"


def test_list_providers_capacity_filtering(repo: SQLiteProviderRepository):
    """Verify querying providers by capacity compatibility."""
    p_small = create_dummy_provider("p_small", min_kw=1.0, max_kw=10.0)
    p_large = create_dummy_provider("p_large", min_kw=50.0, max_kw=500.0)
    repo.upsert_provider(p_small)
    repo.upsert_provider(p_large)

    # Project requiring 5 kW should match p_small (1-10)
    res_5kw = repo.list_providers(min_cap=5.0, max_cap=5.0)
    ids_5kw = [p.provider_id for p in res_5kw]
    assert "p_small" in ids_5kw
    assert "p_large" not in ids_5kw

    # Project requiring 100 kW should match p_large (50-500)
    res_100kw = repo.list_providers(min_cap=100.0, max_cap=100.0)
    ids_100kw = [p.provider_id for p in res_100kw]
    assert "p_large" in ids_100kw
    assert "p_small" not in ids_100kw


def test_delete_provider_cascades_evidence(repo: SQLiteProviderRepository):
    """Verify deleting a provider removes both provider and evidence records."""
    p = create_dummy_provider("p_del")
    repo.upsert_provider(p)
    assert repo.get_provider_by_id("p_del") is not None

    deleted = repo.delete_provider("p_del")
    assert deleted is True
    assert repo.get_provider_by_id("p_del") is None
