"""
Provider Search and Eligibility Service (Stage 1 Filtering).
Applies strict hard gates to disqualify out-of-scope providers before scoring.
"""

from typing import List, Tuple
from src.domain.models import (
    ProjectProfile,
    ProviderRecord,
    ServiceLevel,
    IndiaPresence,
)


class ProviderSearchService:
    """Evaluates hard eligibility gates for candidate solar technology providers."""

    @classmethod
    def evaluate_eligibility(
        cls, profile: ProjectProfile, provider: ProviderRecord
    ) -> Tuple[bool, List[str]]:
        """
        Tests provider against all Stage 1 hard gates.
        Returns:
            (is_eligible, disqualification_reasons)
        """
        reasons: List[str] = []

        # Gate 1: Technology Overlap Gate
        requested_techs = set(profile.technology_preference)
        provider_techs = set(provider.primary_technologies)
        overlap = requested_techs.intersection(provider_techs)
        if not overlap:
            reasons.append(
                f"Technology Mismatch: Provider does not supply requested technologies {list(requested_techs)}. "
                f"Offers {list(provider_techs)}."
            )

        # Gate 2: Capacity Feasibility Gate
        target_kw = profile.target_capacity_kw
        if target_kw < provider.min_capacity_kw or target_kw > provider.max_capacity_kw:
            reasons.append(
                f"Capacity Out of Bounds: Target {target_kw} kW is outside provider's certified range "
                f"({provider.min_capacity_kw} kW - {provider.max_capacity_kw} kW)."
            )

        # Gate 3: Sector Applicability Gate
        if profile.building_type not in provider.supported_building_types:
            reasons.append(
                f"Sector Incompatibility: Provider does not support building type '{profile.building_type.value}'."
            )

        # Gate 4: Minimum India Presence Gate
        if profile.service_requirement in [ServiceLevel.LOCAL_PUNE_OFFICE, ServiceLevel.MAHARASHTRA_SERVICE_NETWORK]:
            if provider.india_presence_type in [IndiaPresence.NONE, IndiaPresence.IMPORT_ONLY_NO_LOCAL_OFFICE]:
                if not provider.pune_service_availability:
                    reasons.append(
                        f"Presence Deficit: Project mandates local presence ({profile.service_requirement.value}), "
                        f"but provider presence tier is '{provider.india_presence_type.value}' without verified Pune support."
                    )

        is_eligible = len(reasons) == 0
        return is_eligible, reasons
