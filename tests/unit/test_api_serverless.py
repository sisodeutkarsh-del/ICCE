"""
Unit tests for Vercel Serverless Function & FastAPI endpoints (api/index.py).
"""

from fastapi.testclient import TestClient
from api.index import app

client = TestClient(app)


def test_api_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app"] == "SolarMatch Pune"
    assert data["total_providers"] >= 6


def test_api_scenarios_endpoint():
    response = client.get("/api/scenarios")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert any("Kothrud" in s["title"] for s in data)


def test_api_options_endpoint():
    response = client.get("/api/options")
    assert response.status_code == 200
    data = response.json()
    assert "building_types" in data
    assert "roof_types" in data
    assert "tech_types" in data


def test_api_providers_endpoint():
    response = client.get("/api/providers?include_sample=false")
    assert response.status_code == 200
    providers = response.json()
    assert len(providers) == 6
    assert all(not p["is_sample_data"] for p in providers)


def test_api_match_endpoint():
    payload = {
        "project_name": "API Test Bungalow",
        "pune_locality": "Baner, Pune",
        "building_type": "RESIDENTIAL_INDIVIDUAL",
        "target_capacity_kw": 6.0,
        "budget_inr": 450000.0,
        "roof_type": "RCC_FLAT",
        "technology_preference": ["MICROINVERTER", "MONO_PERC"],
        "grid_coupling": "ON_GRID_NET_METERED",
        "service_requirement": "LOCAL_PUNE_OFFICE",
        "include_sample": False,
        "trigger_llm_synthesis": False,
    }
    response = client.post("/api/match", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "analysis" in data
    assert "eligible_results" in data
    assert len(data["eligible_results"]) > 0
    assert "markdown_report" in data
    assert "json_report" in data
