"""
Requirement Analysis Service.
Normalizes project profiles, calculates technical rooftop benchmarks for Pune City,
and identifies structural/regulatory constraints under MSEDCL net-metering guidelines.
"""

from typing import Any, Dict
from src.domain.models import ProjectProfile, BuildingType, GridCoupling


class RequirementAnalyzerService:
    """Performs engineering analysis and sizing heuristics for Pune rooftop projects."""

    # Solar insolation metrics for Pune (PMC/PCMC latitude ~18.52° N)
    AVG_PUNE_SPECIFIC_YIELD_KWH_PER_KW_YEAR = 1500.0  # kWh/kWp/year
    ROOF_AREA_SQFT_PER_KW = 100.0  # Approx 100 sq ft (~9.3 sq m) per kW for crystalline PV

    @classmethod
    def analyze_project(cls, profile: ProjectProfile) -> Dict[str, Any]:
        """Calculates expected generation, required area, and regulatory considerations."""
        capacity = profile.target_capacity_kw
        estimated_annual_kwh = capacity * cls.AVG_PUNE_SPECIFIC_YIELD_KWH_PER_KW_YEAR
        estimated_area_sqft = capacity * cls.ROOF_AREA_SQFT_PER_KW
        estimated_area_sqm = estimated_area_sqft * 0.092903

        # Pune regulatory & MSEDCL net-metering guidelines check
        regulatory_notes = []
        if profile.grid_coupling == GridCoupling.ON_GRID_NET_METERED:
            regulatory_notes.append(
                "MSEDCL Net-Metering: Rooftop capacity must not exceed 100% of sanctioned contract demand."
            )
            if capacity > 10.0:
                regulatory_notes.append(
                    "Three-phase connection and bi-directional meter required by MSEDCL for capacities > 10 kW."
                )

        if profile.building_type == BuildingType.HOUSING_SOCIETY:
            regulatory_notes.append(
                "Housing Society (CHS): Requires General Body Resolution (GBM) approval and separate common-meter net connection."
            )

        if profile.building_type in [BuildingType.COMMERCIAL, BuildingType.INDUSTRIAL] and capacity > 100.0:
            regulatory_notes.append(
                "Commercial/Industrial > 100 kW: Electrical Inspector (CEI) approval and anti-islanding relay certification mandatory."
            )

        # Budget sanity calculation if provided
        budget_per_kw = None
        if profile.budget_inr and profile.budget_inr > 0:
            budget_per_kw = profile.budget_inr / capacity

        return {
            "project_id": profile.project_id,
            "project_name": profile.project_name,
            "locality": profile.pune_locality,
            "target_capacity_kw": capacity,
            "estimated_annual_generation_kwh": round(estimated_annual_kwh, 1),
            "estimated_co2_offset_tons_per_year": round((estimated_annual_kwh * 0.82) / 1000.0, 2),
            "estimated_roof_area_sqft": round(estimated_area_sqft, 1),
            "estimated_roof_area_sqm": round(estimated_area_sqm, 1),
            "budget_inr": profile.budget_inr,
            "budget_per_kw_inr": round(budget_per_kw, 2) if budget_per_kw else None,
            "regulatory_notes": regulatory_notes,
        }
