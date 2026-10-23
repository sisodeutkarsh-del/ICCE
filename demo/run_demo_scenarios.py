"""
Demonstration Runner for Phase 8.
Executes the three canonical Pune City rooftop solar matching scenarios
and exports their full reports and evaluation metrics to the demo/ directory.
"""

from pathlib import Path
import json
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
from src.llm.openrouter_adapter import OpenRouterAdapter
from src.llm.gemini_adapter import GeminiAdapter
from src.llm.huggingface_adapter import HuggingFaceAdapter
from src.llm.mock_adapter import MockDeterministicAdapter
from src.llm.fallback_orchestrator import FallbackOrchestrator


def run_demonstration():
    settings = get_settings()
    repo = SQLiteProviderRepository(settings.absolute_db_path)
    
    # Ensure database is seeded
    if repo.count_providers() == 0:
        initialize_database(settings.absolute_db_path)
        importer = DataImporter(repo)
        importer.import_from_json(settings.absolute_verified_data_path)
        importer.import_from_json(settings.absolute_sample_fixtures_path)

    openrouter_adapter = OpenRouterAdapter(api_key=settings.openrouter_api_key, model_id=settings.openrouter_model)
    gemini_adapter = GeminiAdapter(api_key=settings.gemini_api_key, model_id=settings.gemini_model)
    hf_adapter = HuggingFaceAdapter(api_key=settings.huggingface_api_key, model_id=settings.huggingface_model)

    orchestrator = FallbackOrchestrator(
        adapters=[openrouter_adapter, gemini_adapter, hf_adapter],
        max_retries=settings.llm_max_retries,
        backoff_base=settings.llm_backoff_base_seconds,
        default_timeout=settings.llm_timeout_seconds,
    )
    workflow = MatchingAgentWorkflow(repository=repo, orchestrator=orchestrator)

    demo_dir = Path("demo")
    demo_dir.mkdir(exist_ok=True)

    scenarios = [
        {
            "id": "scenario_1_kothrud_chs",
            "name": "Scenario 1: Kothrud Housing Society (35 kW Net-Metered)",
            "profile": ProjectProfile(
                project_id="pune_kothrud_chs",
                project_name="Kothrud Cooperative Housing Society Rooftop",
                pune_locality="Kothrud, Pune",
                building_type=BuildingType.HOUSING_SOCIETY,
                target_capacity_kw=35.0,
                budget_inr=2200000.0,
                roof_type=RoofType.RCC_FLAT,
                technology_preference=[TechType.STRING_INVERTER, TechType.TOPCON],
                grid_coupling=GridCoupling.ON_GRID_NET_METERED,
                service_requirement=ServiceLevel.MAHARASHTRA_SERVICE_NETWORK,
            )
        },
        {
            "id": "scenario_2_baner_bungalow",
            "name": "Scenario 2: Baner Residential Bungalow (6 kW Microinverter)",
            "profile": ProjectProfile(
                project_id="pune_baner_bungalow",
                project_name="Baner Individual Bungalow Solar Installation",
                pune_locality="Baner, Pune",
                building_type=BuildingType.RESIDENTIAL_INDIVIDUAL,
                target_capacity_kw=6.0,
                budget_inr=450000.0,
                roof_type=RoofType.RCC_FLAT,
                technology_preference=[TechType.MICROINVERTER, TechType.MONO_PERC],
                grid_coupling=GridCoupling.ON_GRID_NET_METERED,
                service_requirement=ServiceLevel.LOCAL_PUNE_OFFICE,
            )
        },
        {
            "id": "scenario_3_hinjawadi_commercial",
            "name": "Scenario 3: Hinjawadi Commercial Tech Park (150 kW)",
            "profile": ProjectProfile(
                project_id="pune_hinjawadi_techpark",
                project_name="Hinjawadi IT Park Commercial Rooftop",
                pune_locality="Hinjawadi Phase 1, PCMC",
                building_type=BuildingType.COMMERCIAL,
                target_capacity_kw=150.0,
                budget_inr=9500000.0,
                roof_type=RoofType.METAL_SHED,
                technology_preference=[TechType.STRING_INVERTER, TechType.TOPCON],
                grid_coupling=GridCoupling.ON_GRID_NET_METERED,
                service_requirement=ServiceLevel.MAHARASHTRA_SERVICE_NETWORK,
            )
        }
    ]

    summary_rows = []

    for sc in scenarios:
        print(f"\n=======================================================")
        print(f"Executing: {sc['name']}")
        print(f"=======================================================")
        
        result = workflow.run_workflow(
            sc["profile"],
            include_sample=False,  # Test with verified real providers
            trigger_llm_synthesis=True
        )

        # Save Markdown Report
        md_path = demo_dir / f"{sc['id']}_report.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(result.markdown_report)

        # Save JSON Report
        json_path = demo_dir / f"{sc['id']}_report.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(result.json_report, f, indent=2)

        print(f"Analysis:")
        print(f"  Target Capacity: {result.analysis['target_capacity_kw']} kW")
        print(f"  Est. Generation: {result.analysis['estimated_annual_generation_kwh']:,.0f} kWh/year")
        print(f"  Est. Roof Area:  {result.analysis['estimated_roof_area_sqft']:,.0f} sq.ft")
        print(f"  CO2 Offset:      {result.analysis['estimated_co2_offset_tons_per_year']:.1f} tons/year")
        print(f"\nEligible Matches ({len(result.eligible_results)}):")
        for idx, m in enumerate(result.eligible_results, start=1):
            score = m.compatibility_score
            print(f"  #{idx} {m.provider.name} ({m.provider.headquarters_country})")
            print(f"     Score: {score.total_score:.1f}/100 [{score.score_tier}]")
            print(f"     Tech: {score.tech_fit:.0f}%, Cap: {score.capacity_fit:.0f}%, Svc: {score.service_fit:.0f}%, Cert: {score.cert_fit:.0f}%, Doc: {score.doc_fit:.0f}%")
        
        top_partner = result.eligible_results[0].provider.name if result.eligible_results else "None"
        top_score = result.eligible_results[0].compatibility_score.total_score if result.eligible_results else 0.0

        summary_rows.append({
            "scenario": sc["name"],
            "capacity": f"{sc['profile'].target_capacity_kw} kW",
            "locality": sc["profile"].pune_locality,
            "eligible_count": len(result.eligible_results),
            "disqualified_count": len(result.disqualified_results),
            "top_match": top_partner,
            "top_score": f"{top_score:.1f}/100",
            "report_file": str(md_path)
        })

    print("\n\n=======================================================")
    print("DEMONSTRATION RUN COMPLETE - SUMMARY OF RESULTS")
    print("=======================================================")
    for row in summary_rows:
        print(f"• {row['scenario']}")
        print(f"  Locality: {row['locality']} | Capacity: {row['capacity']}")
        print(f"  Top Match: {row['top_match']} ({row['top_score']}) | Eligible: {row['eligible_count']} | Disqualified: {row['disqualified_count']}")
        print(f"  Report: {row['report_file']}\n")


if __name__ == "__main__":
    run_demonstration()
