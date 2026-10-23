"""
Unit tests for RecommendationReportService and MatchingAgentWorkflow.
Verifies report structure, evidence grounding, UN SDG 7.A alignment, and disclaimer inclusion.
"""

from datetime import date
import json
from pathlib import Path
import pytest
from database.init_db import initialize_database
from src.data.provider_repository import SQLiteProviderRepository
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
from src.services.matching_service import MatchingService
from src.services.agent_workflow import MatchingAgentWorkflow
from src.reports.report_generator import RecommendationReportService


@pytest.fixture
def test_project() -> ProjectProfile:
    return ProjectProfile(
        project_id="test_rep_01",
        project_name="Hadapsar Commercial Rooftop",
        pune_locality="Hadapsar, Pune",
        building_type=BuildingType.COMMERCIAL,
        target_capacity_kw=40.0,
        budget_inr=2600000.0,
        roof_type=RoofType.RCC_FLAT,
        technology_preference=[TechType.STRING_INVERTER],
        grid_coupling=GridCoupling.ON_GRID_NET_METERED,
        service_requirement=ServiceLevel.MAHARASHTRA_SERVICE_NETWORK,
    )


@pytest.fixture
def test_provider() -> ProviderRecord:
    return ProviderRecord(
        provider_id="prv_rep_test",
        name="Munich Inverter AG",
        headquarters_country="Germany",
        primary_technologies=[TechType.STRING_INVERTER],
        min_capacity_kw=10.0,
        max_capacity_kw=100.0,
        supported_building_types=[BuildingType.COMMERCIAL],
        india_presence_type=IndiaPresence.DIRECT_SUBSIDIARY,
        pune_service_availability=True,
        in_country_warehouse=True,
        certifications=["IEC 62109", "BIS CRS Certified"],
        warranty_terms={"years": 10},
        estimated_cost_tier=CostTier.PREMIUM_TIER1,
        is_sample_data=False,
        last_audit_date=date(2026, 10, 1),
        evidence_records=[
            EvidenceCitation(
                citation_id="ev_rep_1",
                claim="Certified 3-phase string inverters for Indian grid conditions.",
                source_url="https://example.com/datasheets/munich-inverter.pdf",
                source_type=SourceType.PRODUCT_DATASHEET,
                last_verified=date(2026, 10, 1),
                verification_note="Audited official datasheet"
            )
        ],
    )


def test_markdown_report_structure(test_project: ProjectProfile, test_provider: ProviderRecord):
    """Verify Markdown report contains all mandatory sections, disclaimers, and evidence."""
    analysis = {
        "target_capacity_kw": 40.0,
        "estimated_annual_generation_kwh": 60000.0,
        "estimated_roof_area_sqft": 4000.0,
        "estimated_roof_area_sqm": 371.6,
        "estimated_co2_offset_tons_per_year": 49.2,
        "regulatory_notes": ["MSEDCL Net-Metering approval required."],
    }
    eligible, disq = MatchingService.match_providers(test_project, [test_provider])
    report_md = RecommendationReportService.generate_markdown_report(
        profile=test_project,
        analysis=analysis,
        eligible_results=eligible,
        disqualified_results=disq,
    )

    assert "INTERNATIONAL SOLAR TECHNOLOGY PARTNER MATCHING REPORT" in report_md
    assert "UN SDG Alignment" in report_md
    assert "Goal 7, Target 7.A" in report_md
    assert "Munich Inverter AG" in report_md
    assert "DISCLAIMER & REGULATORY NOTICE" in report_md
    assert "MSEDCL" in report_md
    assert "https://example.com/datasheets/munich-inverter.pdf" in report_md


def test_json_report_structure(test_project: ProjectProfile, test_provider: ProviderRecord):
    """Verify JSON report generates valid dictionary structure that serializes to JSON."""
    analysis = {
        "target_capacity_kw": 40.0,
        "estimated_annual_generation_kwh": 60000.0,
        "estimated_roof_area_sqft": 4000.0,
    }
    eligible, disq = MatchingService.match_providers(test_project, [test_provider])
    data = RecommendationReportService.generate_json_report(
        profile=test_project,
        analysis=analysis,
        eligible_results=eligible,
        disqualified_results=disq,
    )

    assert "metadata" in data
    assert "project_profile" in data
    assert "eligible_partners" in data
    assert len(data["eligible_partners"]) == 1
    assert data["eligible_partners"][0]["provider_name"] == "Munich Inverter AG"

    # Verify JSON serializability
    serialized = json.dumps(data)
    assert len(serialized) > 200


def test_matching_agent_workflow_e2e(tmp_path: Path, test_project: ProjectProfile, test_provider: ProviderRecord):
    """Verify end-to-end execution of MatchingAgentWorkflow."""
    db_file = tmp_path / "test_wf.db"
    initialize_database(db_file)
    repo = SQLiteProviderRepository(db_file)
    repo.upsert_provider(test_provider)

    workflow = MatchingAgentWorkflow(repository=repo, orchestrator=None)
    result = workflow.run_workflow(test_project, include_sample=True, trigger_llm_synthesis=False)

    assert len(result.eligible_results) == 1
    assert result.eligible_results[0].provider.provider_id == "prv_rep_test"
    assert len(result.markdown_report) > 500
    assert result.json_report["metadata"]["sdg_target"] is not None
