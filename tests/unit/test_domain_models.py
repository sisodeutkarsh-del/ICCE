"""
Unit tests for Domain Models and Pydantic validation rules.
"""

from datetime import date
import pytest
from pydantic import ValidationError
from src.domain.models import (
    ProviderRecord,
    EvidenceCitation,
    ProjectProfile,
    BuildingType,
    RoofType,
    TechType,
    GridCoupling,
    ServiceLevel,
    IndiaPresence,
    CostTier,
    SourceType,
)


def sample_evidence(citation_id="ev_01"):
    return EvidenceCitation(
        citation_id=citation_id,
        claim="Tested module efficiency of 22.5% under STC conditions.",
        source_url="https://example.com/datasheets/module-400.pdf",
        source_type=SourceType.PRODUCT_DATASHEET,
        last_verified=date(2026, 10, 1),
        verification_note="Factory test report audited"
    )


def test_valid_provider_record():
    """Verify that a properly constructed ProviderRecord passes validation."""
    provider = ProviderRecord(
        provider_id="prv_test_01",
        name="Test Solar GmbH",
        headquarters_country="Germany",
        primary_technologies=[TechType.STRING_INVERTER],
        min_capacity_kw=3.0,
        max_capacity_kw=50.0,
        supported_building_types=[BuildingType.RESIDENTIAL_INDIVIDUAL, BuildingType.COMMERCIAL],
        india_presence_type=IndiaPresence.DIRECT_SUBSIDIARY,
        pune_service_availability=True,
        in_country_warehouse=True,
        certifications=["IEC 62109"],
        warranty_terms={"years": 10},
        estimated_cost_tier=CostTier.PREMIUM_TIER1,
        is_sample_data=True,
        last_audit_date=date(2026, 10, 1),
        evidence_records=[sample_evidence()]
    )
    assert provider.provider_id == "prv_test_01"
    assert provider.pune_service_availability is True


def test_provider_record_rejects_inverted_capacity():
    """Verify validation error when min_capacity_kw exceeds max_capacity_kw."""
    with pytest.raises(ValidationError) as exc_info:
        ProviderRecord(
            provider_id="prv_bad_cap",
            name="Bad Capacity Solar",
            headquarters_country="Germany",
            primary_technologies=[TechType.MONO_PERC],
            min_capacity_kw=100.0,
            max_capacity_kw=50.0,  # Invalid: max < min
            supported_building_types=[BuildingType.COMMERCIAL],
            india_presence_type=IndiaPresence.NONE,
            last_audit_date=date(2026, 10, 1),
            evidence_records=[sample_evidence()]
        )
    assert "min_capacity_kw" in str(exc_info.value)


def test_provider_record_rejects_missing_evidence():
    """Verify validation error when evidence_records list is empty."""
    with pytest.raises(ValidationError) as exc_info:
        ProviderRecord(
            provider_id="prv_no_evidence",
            name="No Evidence Brand",
            headquarters_country="Germany",
            primary_technologies=[TechType.STRING_INVERTER],
            min_capacity_kw=1.0,
            max_capacity_kw=10.0,
            supported_building_types=[BuildingType.RESIDENTIAL_INDIVIDUAL],
            india_presence_type=IndiaPresence.DIRECT_SUBSIDIARY,
            last_audit_date=date(2026, 10, 1),
            evidence_records=[]  # Invalid: must have at least 1 citation
        )
    assert "evidence_records" in str(exc_info.value)


def test_provider_record_rejects_invalid_url():
    """Verify validation error when citation source URL is malformed."""
    with pytest.raises(ValidationError) as exc_info:
        EvidenceCitation(
            citation_id="ev_bad_url",
            claim="High efficiency cells",
            source_url="not-a-valid-http-url",
            source_type=SourceType.OFFICIAL_PORTAL,
            last_verified=date(2026, 10, 1)
        )
    assert "source_url" in str(exc_info.value)


def test_project_profile_validation():
    """Verify ProjectProfile validation and locality normalization."""
    profile = ProjectProfile(
        project_id="proj_001",
        project_name="Kothrud Society Solar 50kW",
        pune_locality="  kothrud, pune  ",
        building_type=BuildingType.HOUSING_SOCIETY,
        target_capacity_kw=50.0,
        budget_inr=3000000.0,
        roof_type=RoofType.RCC_FLAT,
        technology_preference=[TechType.TOPCON, TechType.HYBRID_INVERTER],
        grid_coupling=GridCoupling.ON_GRID_NET_METERED,
        service_requirement=ServiceLevel.LOCAL_PUNE_OFFICE
    )
    assert profile.pune_locality == "Kothrud, Pune"
    assert profile.target_capacity_kw == 50.0


def test_project_profile_rejects_invalid_capacity():
    """Verify rejection of zero or excessive capacity."""
    with pytest.raises(ValidationError):
        ProjectProfile(
            project_id="proj_bad",
            project_name="Too Small",
            pune_locality="Baner",
            building_type=BuildingType.RESIDENTIAL_INDIVIDUAL,
            target_capacity_kw=0.1,  # Below min 0.5 kW
            roof_type=RoofType.RCC_FLAT,
            technology_preference=[TechType.MONO_PERC],
            grid_coupling=GridCoupling.ON_GRID_NET_METERED,
            service_requirement=ServiceLevel.MAHARASHTRA_SERVICE_NETWORK
        )
