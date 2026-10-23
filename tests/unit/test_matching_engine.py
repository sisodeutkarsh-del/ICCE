"""
Unit tests for the Deterministic Matching Engine:
- RequirementAnalyzerService
- ProviderSearchService (Stage 1 Hard Filters)
- CompatibilityScoringService (Stage 2 Scoring Formula)
- ExplanationService
- MatchingService (Ranking & Partitioning)
"""

from datetime import date
import pytest
from src.domain.models import (
    ProjectProfile,
    ProviderRecord,
    EvidenceCitation,
    BuildingType,
    RoofType,
    TechType,
    GridCoupling,
    ServiceLevel,
    IndiaPresence,
    CostTier,
    SourceType,
)
from src.services.requirement_analyzer import RequirementAnalyzerService
from src.services.provider_search import ProviderSearchService
from src.services.compatibility_scorer import CompatibilityScoringService
from src.services.explanation_service import ExplanationService
from src.services.matching_service import MatchingService


@pytest.fixture
def residential_project() -> ProjectProfile:
    return ProjectProfile(
        project_id="pune_res_01",
        project_name="Baner Bungalow Solar 6kW",
        pune_locality="Baner, Pune",
        building_type=BuildingType.RESIDENTIAL_INDIVIDUAL,
        target_capacity_kw=6.0,
        budget_inr=450000.0,
        roof_type=RoofType.RCC_FLAT,
        technology_preference=[TechType.MICROINVERTER, TechType.MONO_PERC],
        grid_coupling=GridCoupling.ON_GRID_NET_METERED,
        service_requirement=ServiceLevel.LOCAL_PUNE_OFFICE,
    )


@pytest.fixture
def chs_project() -> ProjectProfile:
    return ProjectProfile(
        project_id="pune_chs_01",
        project_name="Kothrud Housing Society 50kW",
        pune_locality="Kothrud, Pune",
        building_type=BuildingType.HOUSING_SOCIETY,
        target_capacity_kw=50.0,
        budget_inr=3200000.0,
        roof_type=RoofType.RCC_FLAT,
        technology_preference=[TechType.STRING_INVERTER, TechType.TOPCON],
        grid_coupling=GridCoupling.ON_GRID_NET_METERED,
        service_requirement=ServiceLevel.MAHARASHTRA_SERVICE_NETWORK,
    )


def make_provider(
    provider_id: str,
    techs,
    min_kw: float,
    max_kw: float,
    building_types,
    presence=IndiaPresence.DIRECT_SUBSIDIARY,
    pune_svc=True,
    warehouse=True,
    certs=None,
    warranty_terms=None,
    cost_tier=CostTier.PREMIUM_TIER1,
    is_sample=False,
) -> ProviderRecord:
    return ProviderRecord(
        provider_id=provider_id,
        name=f"Provider {provider_id}",
        headquarters_country="Germany",
        primary_technologies=techs,
        min_capacity_kw=min_kw,
        max_capacity_kw=max_kw,
        supported_building_types=building_types,
        india_presence_type=presence,
        pune_service_availability=pune_svc,
        in_country_warehouse=warehouse,
        certifications=certs if certs is not None else ["IEC 62109", "BIS CRS Certified"],
        warranty_terms=warranty_terms if warranty_terms is not None else {"product_years": 10},
        estimated_cost_tier=cost_tier,
        is_sample_data=is_sample,
        last_audit_date=date(2026, 10, 1),
        evidence_records=[
            EvidenceCitation(
                citation_id=f"ev_{provider_id}",
                claim="Certified product specifications",
                source_url="https://example.com/datasheet.pdf",
                source_type=SourceType.PRODUCT_DATASHEET,
                last_verified=date(2026, 10, 1),
            )
        ],
    )


# --- 1. Requirement Analyzer Tests ---

def test_requirement_analyzer_calculations(residential_project: ProjectProfile):
    """Verify Pune generation and roof area calculations."""
    analysis = RequirementAnalyzerService.analyze_project(residential_project)
    # 6 kW * 1500 kWh/kW = 9000 kWh/year
    assert analysis["estimated_annual_generation_kwh"] == 9000.0
    # 6 kW * 100 sqft = 600 sqft
    assert analysis["estimated_roof_area_sqft"] == 600.0
    assert analysis["estimated_co2_offset_tons_per_year"] > 0
    assert len(analysis["regulatory_notes"]) >= 1


# --- 2. Stage 1 Hard Filters Tests ---

def test_hard_filter_technology_mismatch(residential_project: ProjectProfile):
    """Provider supplying only BESS is disqualified when project requires MICROINVERTER and MONO_PERC."""
    provider = make_provider(
        "prv_bess_only",
        techs=[TechType.BESS_LFP],
        min_kw=1.0,
        max_kw=50.0,
        building_types=[BuildingType.RESIDENTIAL_INDIVIDUAL],
    )
    is_eligible, reasons = ProviderSearchService.evaluate_eligibility(residential_project, provider)
    assert is_eligible is False
    assert any("Technology Mismatch" in r for r in reasons)


def test_hard_filter_capacity_out_of_bounds(residential_project: ProjectProfile):
    """Provider certified for 50 - 500 kW is disqualified for a 6 kW residential project."""
    provider = make_provider(
        "prv_commercial_only",
        techs=[TechType.MICROINVERTER],
        min_kw=50.0,
        max_kw=500.0,
        building_types=[BuildingType.RESIDENTIAL_INDIVIDUAL],
    )
    is_eligible, reasons = ProviderSearchService.evaluate_eligibility(residential_project, provider)
    assert is_eligible is False
    assert any("Capacity Out of Bounds" in r for r in reasons)


def test_hard_filter_sector_incompatibility(residential_project: ProjectProfile):
    """Provider supporting only INDUSTRIAL is disqualified for RESIDENTIAL_INDIVIDUAL."""
    provider = make_provider(
        "prv_ind_only",
        techs=[TechType.MICROINVERTER],
        min_kw=1.0,
        max_kw=50.0,
        building_types=[BuildingType.INDUSTRIAL],
    )
    is_eligible, reasons = ProviderSearchService.evaluate_eligibility(residential_project, provider)
    assert is_eligible is False
    assert any("Sector Incompatibility" in r for r in reasons)


def test_hard_filter_presence_gate_rejection(residential_project: ProjectProfile):
    """Provider with IMPORT_ONLY and no Pune service is rejected when project requires LOCAL_PUNE_OFFICE."""
    provider = make_provider(
        "prv_remote_only",
        techs=[TechType.MICROINVERTER],
        min_kw=1.0,
        max_kw=20.0,
        building_types=[BuildingType.RESIDENTIAL_INDIVIDUAL],
        presence=IndiaPresence.IMPORT_ONLY_NO_LOCAL_OFFICE,
        pune_svc=False,
    )
    is_eligible, reasons = ProviderSearchService.evaluate_eligibility(residential_project, provider)
    assert is_eligible is False
    assert any("Presence Deficit" in r for r in reasons)


# --- 3. Stage 2 Compatibility Scoring Tests ---

def test_exact_tech_fit_scoring(residential_project: ProjectProfile):
    """Project wants [MICROINVERTER, MONO_PERC]. Provider offers only MICROINVERTER -> 50% overlap."""
    provider = make_provider(
        "prv_half_tech",
        techs=[TechType.MICROINVERTER],
        min_kw=1.0,
        max_kw=20.0,
        building_types=[BuildingType.RESIDENTIAL_INDIVIDUAL],
    )
    score_tech = CompatibilityScoringService.calculate_tech_fit(residential_project, provider)
    assert score_tech == 50.0


def test_capacity_fit_sweet_spot_vs_boundary(residential_project: ProjectProfile):
    """Target 6 kW: Sweet spot [1.5*1=1.5, 0.8*20=16] -> 100.0 score."""
    p_sweet = make_provider("prv_sweet", [TechType.MICROINVERTER], 1.0, 20.0, [BuildingType.RESIDENTIAL_INDIVIDUAL])
    assert CompatibilityScoringService.calculate_capacity_fit(residential_project, p_sweet) == 100.0

    # Project 6 kW on provider min 5 kW, max 10 kW -> lower boundary region decay
    p_edge = make_provider("prv_edge", [TechType.MICROINVERTER], 5.0, 10.0, [BuildingType.RESIDENTIAL_INDIVIDUAL])
    score_edge = CompatibilityScoringService.calculate_capacity_fit(residential_project, p_edge)
    assert 60.0 <= score_edge < 100.0


def test_service_fit_scores():
    """Verify service fit grading based on Pune availability and warehouse."""
    p_full = make_provider("prv_s1", [TechType.TOPCON], 1.0, 100.0, [BuildingType.HOUSING_SOCIETY], pune_svc=True, warehouse=True)
    assert CompatibilityScoringService.calculate_service_fit(None, p_full) == 100.0

    p_no_wh = make_provider("prv_s2", [TechType.TOPCON], 1.0, 100.0, [BuildingType.HOUSING_SOCIETY], pune_svc=True, warehouse=False)
    assert CompatibilityScoringService.calculate_service_fit(None, p_no_wh) == 90.0

    p_remote = make_provider("prv_s3", [TechType.TOPCON], 1.0, 100.0, [BuildingType.HOUSING_SOCIETY], presence=IndiaPresence.IMPORT_ONLY_NO_LOCAL_OFFICE, pune_svc=False, warehouse=False)
    assert CompatibilityScoringService.calculate_service_fit(None, p_remote) == 40.0


def test_missing_data_penalty():
    """Provider missing warehouse and certifications incurs penalty."""
    p = make_provider(
        "prv_missing",
        [TechType.TOPCON],
        1.0,
        100.0,
        [BuildingType.HOUSING_SOCIETY],
        warehouse=False,
        pune_svc=False,
        certs=[],
        warranty_terms={},
    )
    penalty, missing = CompatibilityScoringService.compute_missing_penalty(p)
    assert penalty == 20.0  # 4 missing fields * 5.0
    assert len(missing) == 4


# --- 4. Matching Service Pipeline & Ranking Tests ---

def test_matching_service_ranking(chs_project: ProjectProfile):
    """Verify that eligible providers are ranked in descending order of compatibility score."""
    p_top = make_provider(
        "prv_best",
        techs=[TechType.STRING_INVERTER, TechType.TOPCON],
        min_kw=10.0,
        max_kw=100.0,
        building_types=[BuildingType.HOUSING_SOCIETY],
        presence=IndiaPresence.DIRECT_SUBSIDIARY,
        pune_svc=True,
        warehouse=True,
    )
    p_mid = make_provider(
        "prv_second",
        techs=[TechType.STRING_INVERTER],  # 50% tech match
        min_kw=10.0,
        max_kw=100.0,
        building_types=[BuildingType.HOUSING_SOCIETY],
        presence=IndiaPresence.AUTHORIZED_DISTRIBUTOR,
        pune_svc=False,
        warehouse=False,
    )
    p_disqualified = make_provider(
        "prv_disq",
        techs=[TechType.HJT],  # 0% match
        min_kw=10.0,
        max_kw=100.0,
        building_types=[BuildingType.HOUSING_SOCIETY],
    )

    eligible, disqualified = MatchingService.match_providers(chs_project, [p_mid, p_disqualified, p_top])

    assert len(eligible) == 2
    assert len(disqualified) == 1
    assert disqualified[0].provider.provider_id == "prv_disq"

    # p_top must rank higher than p_mid
    assert eligible[0].provider.provider_id == "prv_best"
    assert eligible[1].provider.provider_id == "prv_second"
    assert eligible[0].compatibility_score.total_score > eligible[1].compatibility_score.total_score
    assert len(eligible[0].positive_drivers) >= 1
