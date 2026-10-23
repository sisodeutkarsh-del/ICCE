"""
Explanation Service.
Generates deterministic, evidence-grounded justifications, identifies score drivers,
and flags due-diligence risks and missing information for matched solar technology partners.
"""

from typing import List, Tuple
from src.domain.models import ProjectProfile, ProviderRecord, CompatibilityScore
from src.services.compatibility_scorer import CompatibilityScoringService


class ExplanationService:
    """Generates explainability metadata for provider evaluation."""

    @classmethod
    def generate_explanations(
        cls, profile: ProjectProfile, provider: ProviderRecord, score: CompatibilityScore
    ) -> Tuple[List[str], List[str], List[str]]:
        """
        Synthesizes positive drivers, risk flags, and missing data items.
        Returns:
            (positive_drivers, risk_flags, missing_fields)
        """
        positive_drivers: List[str] = []
        risk_flags: List[str] = []

        _, missing_fields = CompatibilityScoringService.compute_missing_penalty(provider)

        # 1. Technology Driver
        if score.tech_fit == 100.0:
            positive_drivers.append(
                f"Complete technology coverage for requested components: {[t.value for t in profile.technology_preference]}."
            )
        elif score.tech_fit >= 50.0:
            positive_drivers.append(
                f"Partial technology overlap ({score.tech_fit}%) with requested system specifications."
            )

        # 2. Service & Pune Presence Driver / Risk
        if provider.pune_service_availability and provider.in_country_warehouse:
            positive_drivers.append(
                "Direct local Pune service support and active in-country spare parts warehouse."
            )
        elif provider.pune_service_availability:
            positive_drivers.append("Verified local technical channel / service partner in Pune / PCMC.")
        else:
            risk_flags.append(
                f"No verified local office in Pune; support relies on {provider.india_presence_type.value} structure."
            )

        # 3. Capacity Scale Driver / Risk
        if score.capacity_fit == 100.0:
            positive_drivers.append(
                f"Target capacity ({profile.target_capacity_kw} kW) sits inside provider's optimal operating range."
            )
        elif score.capacity_fit < 75.0:
            risk_flags.append(
                f"Project scale ({profile.target_capacity_kw} kW) is near manufacturer's certified limit "
                f"({provider.min_capacity_kw} - {provider.max_capacity_kw} kW)."
            )

        # 4. Certifications Driver
        if score.cert_fit == 100.0:
            positive_drivers.append(
                "Full dual compliance: Bureau of Indian Standards (BIS CRS) and International Electrotechnical Commission (IEC)."
            )
        elif score.cert_fit < 60.0:
            risk_flags.append(
                "Limited certification evidence verified in Indian registry; MSEDCL net-metering approval may require EPC diligence."
            )

        # 5. Cost Alignment
        if profile.budget_inr:
            if score.cost_fit == 100.0:
                positive_drivers.append(
                    f"Cost tier ({provider.estimated_cost_tier.value}) strongly aligns with project budget allocation."
                )
            elif score.cost_fit < 65.0:
                risk_flags.append(
                    f"Potential cost mismatch: Provider cost tier ({provider.estimated_cost_tier.value}) diverges from allocated budget."
                )

        # 6. Sample Data Warning
        if provider.is_sample_data:
            risk_flags.append(
                "NOTICE: This provider profile is marked as synthetic sample test data and must not be used for real procurement."
            )

        return positive_drivers, risk_flags, missing_fields
