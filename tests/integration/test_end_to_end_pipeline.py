"""
Comprehensive End-to-End Integration and Edge-Case Test Suite.
Validates realistic Pune scenarios, capacity boundary limits, zero-match resilience,
offline execution, and secret redaction audit.
"""

from pathlib import Path
import json
import pytest
from config.settings import get_settings
from database.init_db import initialize_database
from src.data.provider_repository import SQLiteProviderRepository
from src.data.importer import DataImporter
from src.domain.models import (
    ProjectProfile,
    BuildingType,
    RoofType,
    TechType,
    GridCoupling,
    ServiceLevel,
)
from src.services.agent_workflow import MatchingAgentWorkflow


@pytest.fixture(scope="module")
def seeded_repo(tmp_path_factory) -> SQLiteProviderRepository:
    """Creates a temporary seeded database with verified and sample fixtures."""
    db_dir = tmp_path_factory.mktemp("integration_db")
    db_path = db_dir / "integration_solar.db"
    initialize_database(db_path)

    repo = SQLiteProviderRepository(db_path)
    importer = DataImporter(repo)

    settings = get_settings()
    importer.import_from_json(settings.absolute_verified_data_path)
    importer.import_from_json(settings.absolute_sample_fixtures_path)

    assert repo.count_providers() >= 9
    return repo


# --- 1. Realistic Pune Project Scenario Tests ---

def test_e2e_residential_pipeline(seeded_repo: SQLiteProviderRepository):
    """Scenario 1: Residential Bungalow in Baner, Pune (6 kW, Microinverter + Mono PERC)."""
    profile = ProjectProfile(
        project_id="pune_baner_01",
        project_name="Baner Bungalow Solar Installation",
        pune_locality="Baner, Pune",
        building_type=BuildingType.RESIDENTIAL_INDIVIDUAL,
        target_capacity_kw=6.0,
        budget_inr=450000.0,
        roof_type=RoofType.RCC_FLAT,
        technology_preference=[TechType.MICROINVERTER, TechType.MONO_PERC],
        grid_coupling=GridCoupling.ON_GRID_NET_METERED,
        service_requirement=ServiceLevel.LOCAL_PUNE_OFFICE,
    )

    wf = MatchingAgentWorkflow(repository=seeded_repo, orchestrator=None)
    res = wf.run_workflow(profile, include_sample=True, trigger_llm_synthesis=False)

    assert len(res.eligible_results) >= 1
    # Enphase should be amongst top matches for residential microinverter in Pune
    top_provider_ids = [m.provider.provider_id for m in res.eligible_results]
    assert "prv_enphase_energy_us" in top_provider_ids

    # Check sizing calculation
    assert res.analysis["estimated_annual_generation_kwh"] == 9000.0
    assert "INTERNATIONAL SOLAR TECHNOLOGY PARTNER MATCHING REPORT" in res.markdown_report
    assert "Baner, Pune" in res.markdown_report


def test_e2e_housing_society_pipeline(seeded_repo: SQLiteProviderRepository):
    """Scenario 2: Housing Society in Kothrud, Pune (35 kW Net-Metered, Common Area)."""
    profile = ProjectProfile(
        project_id="pune_kothrud_chs",
        project_name="Kothrud Housing Society Common Solar",
        pune_locality="Kothrud, Pune",
        building_type=BuildingType.HOUSING_SOCIETY,
        target_capacity_kw=35.0,
        budget_inr=2200000.0,
        roof_type=RoofType.RCC_FLAT,
        technology_preference=[TechType.STRING_INVERTER, TechType.TOPCON],
        grid_coupling=GridCoupling.ON_GRID_NET_METERED,
        service_requirement=ServiceLevel.MAHARASHTRA_SERVICE_NETWORK,
    )

    wf = MatchingAgentWorkflow(repository=seeded_repo, orchestrator=None)
    res = wf.run_workflow(profile, include_sample=False, trigger_llm_synthesis=False)

    assert len(res.eligible_results) >= 3
    # Check that MSEDCL society note is present
    assert any("Housing Society (CHS)" in n for n in res.analysis["regulatory_notes"])
    # Check that highest score partner has score >= 75
    assert res.eligible_results[0].compatibility_score.total_score >= 75.0


def test_e2e_commercial_pipeline(seeded_repo: SQLiteProviderRepository):
    """Scenario 3: Commercial Tech Park in Hinjawadi, PCMC (150 kW, String Inverter)."""
    profile = ProjectProfile(
        project_id="pune_hinjawadi_comm",
        project_name="Hinjawadi IT Park Solar",
        pune_locality="Hinjawadi, PCMC",
        building_type=BuildingType.COMMERCIAL,
        target_capacity_kw=150.0,
        budget_inr=9500000.0,
        roof_type=RoofType.METAL_SHED,
        technology_preference=[TechType.STRING_INVERTER, TechType.TOPCON],
        grid_coupling=GridCoupling.ON_GRID_NET_METERED,
        service_requirement=ServiceLevel.MAHARASHTRA_SERVICE_NETWORK,
    )

    wf = MatchingAgentWorkflow(repository=seeded_repo, orchestrator=None)
    res = wf.run_workflow(profile, include_sample=True, trigger_llm_synthesis=False)

    assert len(res.eligible_results) >= 2
    # Verify CEI commercial > 100 kW note
    assert any("Electrical Inspector (CEI)" in n for n in res.analysis["regulatory_notes"])


# --- 2. Capacity Boundary Edge-Case Tests ---

def test_e2e_micro_capacity_boundary(seeded_repo: SQLiteProviderRepository):
    """Test lower boundary limit: 1.0 kW micro-residential installation."""
    profile = ProjectProfile(
        project_id="pune_micro_01",
        project_name="Micro Residential Rooftop",
        pune_locality="Aundh, Pune",
        building_type=BuildingType.RESIDENTIAL_INDIVIDUAL,
        target_capacity_kw=1.0,
        roof_type=RoofType.RCC_FLAT,
        technology_preference=[TechType.MICROINVERTER],
        grid_coupling=GridCoupling.ON_GRID_NET_METERED,
        service_requirement=ServiceLevel.LOCAL_PUNE_OFFICE,
    )

    wf = MatchingAgentWorkflow(repository=seeded_repo, orchestrator=None)
    res = wf.run_workflow(profile, include_sample=True, trigger_llm_synthesis=False)

    assert res.analysis["estimated_annual_generation_kwh"] == 1500.0
    assert len(res.eligible_results) >= 1


def test_e2e_megawatt_capacity_boundary(seeded_repo: SQLiteProviderRepository):
    """Test upper boundary limit: 1500.0 kW multi-megawatt industrial installation."""
    profile = ProjectProfile(
        project_id="pune_mega_01",
        project_name="Bhosari Industrial Megawatt Solar",
        pune_locality="Bhosari MIDC, PCMC",
        building_type=BuildingType.INDUSTRIAL,
        target_capacity_kw=1500.0,
        roof_type=RoofType.METAL_SHED,
        technology_preference=[TechType.TOPCON],
        grid_coupling=GridCoupling.ON_GRID_NET_METERED,
        service_requirement=ServiceLevel.MAHARASHTRA_SERVICE_NETWORK,
    )

    wf = MatchingAgentWorkflow(repository=seeded_repo, orchestrator=None)
    res = wf.run_workflow(profile, include_sample=False, trigger_llm_synthesis=False)

    assert len(res.eligible_results) >= 1
    # Module manufacturers supporting MW scale like Trina or LONGi should be eligible
    eligible_names = [m.provider.name for m in res.eligible_results]
    assert any("LONGi" in name or "Trina" in name for name in eligible_names)


# --- 3. Zero-Match Resilience Test ---

def test_e2e_zero_match_resilience(seeded_repo: SQLiteProviderRepository):
    """Verify that impossible constraints (e.g., 2200 kW microinverters) produce clear guidance without error."""
    profile = ProjectProfile(
        project_id="pune_zero_match",
        project_name="Impossible Spec Solar",
        pune_locality="Viman Nagar, Pune",
        building_type=BuildingType.COMMERCIAL,
        target_capacity_kw=2200.0,  # Far above microinverter limits
        roof_type=RoofType.RCC_FLAT,
        technology_preference=[TechType.MICROINVERTER],
        grid_coupling=GridCoupling.ON_GRID_NET_METERED,
        service_requirement=ServiceLevel.LOCAL_PUNE_OFFICE,
    )

    wf = MatchingAgentWorkflow(repository=seeded_repo, orchestrator=None)
    res = wf.run_workflow(profile, include_sample=True, trigger_llm_synthesis=False)

    assert len(res.eligible_results) == 0
    assert len(res.disqualified_results) >= 1
    assert "No international providers met all Stage 1 hard eligibility gates" in res.markdown_report


# --- 4. 100% Offline Execution Guarantee ---

def test_e2e_offline_execution_guarantee(seeded_repo: SQLiteProviderRepository):
    """Verify workflow executes completely with orchestrator=None (zero API keys, offline)."""
    profile = ProjectProfile(
        project_id="pune_offline_test",
        project_name="Offline Test Project",
        pune_locality="Hadapsar, Pune",
        building_type=BuildingType.HOUSING_SOCIETY,
        target_capacity_kw=20.0,
        roof_type=RoofType.RCC_FLAT,
        technology_preference=[TechType.STRING_INVERTER],
        grid_coupling=GridCoupling.ON_GRID_NET_METERED,
        service_requirement=ServiceLevel.PAN_INDIA_AUTHORIZED_PARTNER,
    )

    wf = MatchingAgentWorkflow(repository=seeded_repo, orchestrator=None)
    res = wf.run_workflow(profile, include_sample=True, trigger_llm_synthesis=False)

    assert res.markdown_report is not None
    assert len(res.markdown_report) > 500
    assert res.json_report["metadata"]["sdg_target"] is not None


# --- 5. Security & Secret Protection Audit ---

def test_security_audit_zero_secret_leak(seeded_repo: SQLiteProviderRepository):
    """Audit generated reports and data outputs to ensure no raw secrets are leaked."""
    settings = get_settings()
    profile = ProjectProfile(
        project_id="pune_sec_audit",
        project_name="Security Audit Profile",
        pune_locality="Kothrud, Pune",
        building_type=BuildingType.RESIDENTIAL_INDIVIDUAL,
        target_capacity_kw=5.0,
        roof_type=RoofType.RCC_FLAT,
        technology_preference=[TechType.STRING_INVERTER],
        grid_coupling=GridCoupling.ON_GRID_NET_METERED,
        service_requirement=ServiceLevel.LOCAL_PUNE_OFFICE,
    )

    wf = MatchingAgentWorkflow(repository=seeded_repo, orchestrator=None)
    res = wf.run_workflow(profile, include_sample=True, trigger_llm_synthesis=False)

    # Inspect generated markdown and json report strings
    md_text = res.markdown_report
    json_text = json.dumps(res.json_report)

    # Known secret prefixes that must NEVER appear in unmasked form
    forbidden_tokens = []
    if settings.openrouter_api_key:
        forbidden_tokens.append(settings.openrouter_api_key)
    if settings.huggingface_api_key:
        forbidden_tokens.append(settings.huggingface_api_key)
    if settings.gemini_api_key:
        forbidden_tokens.append(settings.gemini_api_key)

    for token in forbidden_tokens:
        assert token not in md_text, "CRITICAL: Raw API key leaked in Markdown report!"
        assert token not in json_text, "CRITICAL: Raw API key leaked in JSON report!"
