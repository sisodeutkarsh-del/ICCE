"""
Vercel Serverless Function entry point & FastAPI application
for SolarMatch Pune - AI International Solar Technology Partner Matching Agent.
Targeted at Pune City, Maharashtra (UN SDG 7.A).
"""

import sys
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# Ensure repository root is on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config.settings import get_settings
from database.seed_db import seed_database
from src.data.provider_repository import SQLiteProviderRepository
from src.domain.models import (
    BuildingType,
    CostTier,
    GridCoupling,
    IndiaPresence,
    ProjectProfile,
    RoofType,
    ServiceLevel,
    TechType,
)
from src.llm import FallbackOrchestrator, GeminiAdapter, HuggingFaceAdapter, OpenRouterAdapter
from src.services.agent_workflow import MatchingAgentWorkflow

app = FastAPI(
    title="SolarMatch Pune API",
    description="Deterministic and evidence-grounded solar partner matching under UN SDG 7.A",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_repo: Optional[SQLiteProviderRepository] = None
_workflow: Optional[MatchingAgentWorkflow] = None


def get_repository() -> SQLiteProviderRepository:
    """Lazily initializes repository and seeds database if needed (e.g. on /tmp in Vercel)."""
    global _repo
    if _repo is None:
        settings = get_settings()
        db_path = settings.absolute_db_path
        if not db_path.exists():
            seed_database()
        _repo = SQLiteProviderRepository(db_path)
    return _repo


def get_workflow() -> MatchingAgentWorkflow:
    """Lazily initializes the matching workflow and fallback orchestrator."""
    global _workflow
    if _workflow is None:
        repo = get_repository()
        settings = get_settings()
        openrouter = OpenRouterAdapter(api_key=settings.openrouter_api_key, model_id=settings.openrouter_model)
        gemini = GeminiAdapter(api_key=settings.gemini_api_key, model_id=settings.gemini_model)
        hf = HuggingFaceAdapter(api_key=settings.huggingface_api_key, model_id=settings.huggingface_model)
        orchestrator = FallbackOrchestrator(
            adapters=[openrouter, gemini, hf],
            max_retries=settings.llm_max_retries,
            backoff_base=settings.llm_backoff_base_seconds,
            default_timeout=settings.llm_timeout_seconds,
        )
        _workflow = MatchingAgentWorkflow(repository=repo, orchestrator=orchestrator)
    return _workflow


# Predefined realistic Pune scenarios
PUNE_SCENARIOS = {
    "kothrud_chs": {
        "id": "kothrud_chs",
        "title": "Scenario 1: Kothrud Housing Society (35 kW Net-Metered)",
        "name": "Kothrud Cooperative Housing Society Rooftop",
        "locality": "Kothrud, Pune",
        "building_type": BuildingType.HOUSING_SOCIETY.value,
        "target_capacity_kw": 35.0,
        "budget_inr": 2200000.0,
        "roof_type": RoofType.RCC_FLAT.value,
        "technologies": [TechType.STRING_INVERTER.value, TechType.TOPCON.value],
        "grid_coupling": GridCoupling.ON_GRID_NET_METERED.value,
        "service_requirement": ServiceLevel.MAHARASHTRA_SERVICE_NETWORK.value,
        "description": "Mid-scale common-meter rooftop project for a cooperative residential society complying with MSEDCL net metering and GBM consensus.",
    },
    "baner_bungalow": {
        "id": "baner_bungalow",
        "title": "Scenario 2: Baner Residential Bungalow (6 kW Microinverter)",
        "name": "Baner Individual Bungalow Solar",
        "locality": "Baner, Pune",
        "building_type": BuildingType.RESIDENTIAL_INDIVIDUAL.value,
        "target_capacity_kw": 6.0,
        "budget_inr": 450000.0,
        "roof_type": RoofType.RCC_FLAT.value,
        "technologies": [TechType.MICROINVERTER.value, TechType.MONO_PERC.value],
        "grid_coupling": GridCoupling.ON_GRID_NET_METERED.value,
        "service_requirement": ServiceLevel.LOCAL_PUNE_OFFICE.value,
        "description": "Small-scale residential system with microinverters for shade resilience and high modularity in Pune's urban bungalows.",
    },
    "hinjawadi_it_park": {
        "id": "hinjawadi_it_park",
        "title": "Scenario 3: Hinjawadi Commercial IT Tech Park (150 kW)",
        "name": "Hinjawadi IT Park Commercial Rooftop",
        "locality": "Hinjawadi Phase 1, PCMC",
        "building_type": BuildingType.COMMERCIAL.value,
        "target_capacity_kw": 150.0,
        "budget_inr": 9500000.0,
        "roof_type": RoofType.METAL_SHED.value,
        "technologies": [TechType.STRING_INVERTER.value, TechType.TOPCON.value],
        "grid_coupling": GridCoupling.ON_GRID_NET_METERED.value,
        "service_requirement": ServiceLevel.MAHARASHTRA_SERVICE_NETWORK.value,
        "description": "Commercial metal-shed rooftop requiring megawatt-grade inverters, CEI safety clearance, and rapid industrial payback.",
    },
}


class MatchRequestBody(BaseModel):
    project_name: str = Field(..., min_length=3, max_length=100)
    pune_locality: str = Field(..., min_length=2)
    building_type: BuildingType
    target_capacity_kw: float = Field(..., ge=0.5, le=5000.0)
    budget_inr: Optional[float] = Field(default=None, gt=0)
    roof_type: RoofType
    technology_preference: List[TechType] = Field(..., min_length=1)
    grid_coupling: GridCoupling
    service_requirement: ServiceLevel
    priority_weights: Optional[Dict[str, float]] = None
    include_sample: bool = False
    trigger_llm_synthesis: bool = True


@app.get("/api/health")
def health_check():
    """Health status and database metrics."""
    try:
        repo = get_repository()
        total = repo.count_providers(include_sample=True)
        verified = repo.count_providers(include_sample=False)
        return {
            "status": "healthy",
            "app": "SolarMatch Pune",
            "sdg_target": "UN SDG 7.A Clean Energy Cooperation",
            "total_providers": total,
            "verified_providers": verified,
            "sample_providers": total - verified,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/scenarios")
def get_scenarios():
    """Pre-configured realistic Pune rooftop solar scenarios."""
    return list(PUNE_SCENARIOS.values())


@app.get("/api/options")
def get_form_options():
    """Available enum options for project intake forms."""
    return {
        "building_types": [{"value": b.value, "label": b.value.replace("_", " ").title()} for b in BuildingType],
        "roof_types": [{"value": r.value, "label": r.value.replace("_", " ").title()} for r in RoofType],
        "tech_types": [{"value": t.value, "label": t.value.replace("_", " ")} for t in TechType],
        "grid_couplings": [{"value": g.value, "label": g.value.replace("_", " ").title()} for g in GridCoupling],
        "service_levels": [{"value": s.value, "label": s.value.replace("_", " ").title()} for s in ServiceLevel],
    }


@app.get("/api/providers")
def list_providers(include_sample: bool = Query(default=False)):
    """Catalog of verified international clean technology providers."""
    repo = get_repository()
    providers = repo.list_providers(include_sample=include_sample)
    return [p.model_dump(mode="json") for p in providers]


@app.post("/api/match")
def run_matching(payload: MatchRequestBody):
    """Executes technical sizing, Stage 1 eligibility filtering, Stage 2 scoring, and report generation."""
    try:
        profile = ProjectProfile(
            project_id=f"proj_{uuid.uuid4().hex[:8]}",
            project_name=payload.project_name.strip(),
            pune_locality=payload.pune_locality.strip(),
            building_type=payload.building_type,
            target_capacity_kw=payload.target_capacity_kw,
            budget_inr=payload.budget_inr,
            roof_type=payload.roof_type,
            technology_preference=payload.technology_preference,
            grid_coupling=payload.grid_coupling,
            service_requirement=payload.service_requirement,
            priority_weights=payload.priority_weights,
        )

        workflow = get_workflow()
        result = workflow.run_workflow(
            profile=profile,
            include_sample=payload.include_sample,
            trigger_llm_synthesis=payload.trigger_llm_synthesis,
        )

        return result.model_dump(mode="json")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# Mount static files when running locally (FastAPI dev server)
PUBLIC_DIR = BASE_DIR / "public"
if PUBLIC_DIR.exists():
    app.mount("/", StaticFiles(directory=str(PUBLIC_DIR), html=True), name="public")
