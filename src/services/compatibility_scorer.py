"""
Compatibility Scoring Service (Stage 2 Scoring).
Computes mathematically verifiable, multi-criteria compatibility scores between
a Pune project profile and qualified candidate technology providers.
"""

from datetime import date
from typing import Dict, List, Optional, Tuple
from src.domain.models import (
    ProjectProfile,
    ProviderRecord,
    CompatibilityScore,
    IndiaPresence,
    CostTier,
    SourceType,
)


DEFAULT_WEIGHTS: Dict[str, float] = {
    "tech": 0.25,
    "capacity": 0.20,
    "service": 0.20,
    "cert": 0.15,
    "doc": 0.10,
    "cost": 0.10,
}

COST_TIER_BENCHMARKS = {
    CostTier.ECONOMY: 48000.0,           # INR/kW
    CostTier.MID_RANGE: 62000.0,         # INR/kW
    CostTier.PREMIUM_TIER1: 82000.0,     # INR/kW
    CostTier.HIGH_END_SPECIALTY: 110000.0 # INR/kW
}


class CompatibilityScoringService:
    """Calculates granular compatibility sub-scores and aggregate weighted score."""

    @classmethod
    def calculate_tech_fit(cls, profile: ProjectProfile, provider: ProviderRecord) -> float:
        """Measures percentage overlap of requested technologies provided by manufacturer."""
        req = set(profile.technology_preference)
        avail = set(provider.primary_technologies)
        if not req:
            return 100.0
        overlap = req.intersection(avail)
        return round((len(overlap) / len(req)) * 100.0, 1)

    @classmethod
    def calculate_capacity_fit(cls, profile: ProjectProfile, provider: ProviderRecord) -> float:
        """
        Evaluates proximity of project scale to provider's optimal operating sweet spot.
        Sweet spot is defined as [1.5 * min_capacity, 0.8 * max_capacity].
        """
        c = profile.target_capacity_kw
        p_min = provider.min_capacity_kw
        p_max = provider.max_capacity_kw

        if c < p_min or c > p_max:
            return 0.0  # Outside bounds

        low_sweet = min(p_min * 1.5, p_max)
        high_sweet = max(p_max * 0.8, p_min)

        if low_sweet <= c <= high_sweet:
            return 100.0
        elif c < low_sweet:
            denom = max(low_sweet - p_min, 0.001)
            ratio = (c - p_min) / denom
            return round(60.0 + (40.0 * max(0.0, min(ratio, 1.0))), 1)
        else:
            denom = max(p_max - high_sweet, 0.001)
            ratio = (p_max - c) / denom
            return round(60.0 + (40.0 * max(0.0, min(ratio, 1.0))), 1)

    @classmethod
    def calculate_service_fit(cls, profile: ProjectProfile, provider: ProviderRecord) -> float:
        """Evaluates verified presence in India and local service availability in Pune."""
        if provider.pune_service_availability and provider.in_country_warehouse:
            return 100.0
        elif provider.pune_service_availability:
            return 90.0
        elif provider.india_presence_type == IndiaPresence.DIRECT_SUBSIDIARY:
            return 85.0
        elif provider.india_presence_type == IndiaPresence.AUTHORIZED_DISTRIBUTOR:
            return 70.0
        elif provider.india_presence_type == IndiaPresence.CERTIFIED_EPC_NETWORK:
            return 60.0
        elif provider.india_presence_type == IndiaPresence.IMPORT_ONLY_NO_LOCAL_OFFICE:
            return 40.0
        return 15.0

    @classmethod
    def calculate_cert_fit(cls, provider: ProviderRecord) -> float:
        """Evaluates compliance with Indian grid requirements (BIS CRS) and IEC standards."""
        certs_str = " ".join(provider.certifications).upper()
        has_bis = "BIS" in certs_str
        has_iec = "IEC" in certs_str

        if has_bis and has_iec:
            return 100.0
        elif has_bis or has_iec:
            return 80.0
        elif len(provider.certifications) > 0:
            return 60.0
        return 30.0

    @classmethod
    def calculate_doc_fit(cls, provider: ProviderRecord) -> float:
        """Scores depth and currency of verifiable documentation and datasheets."""
        ev_count = len(provider.evidence_records)
        base = min(ev_count * 25.0, 75.0)

        # Bonus for official portal or datasheet
        has_official = any(
            ev.source_type in [SourceType.PRODUCT_DATASHEET, SourceType.OFFICIAL_PORTAL]
            for ev in provider.evidence_records
        )
        bonus_official = 15.0 if has_official else 0.0

        # Audit recency bonus (within 365 days)
        days_since_audit = (date.today() - provider.last_audit_date).days
        bonus_recent = 10.0 if days_since_audit <= 365 else 0.0

        return min(round(base + bonus_official + bonus_recent, 1), 100.0)

    @classmethod
    def calculate_cost_fit(cls, profile: ProjectProfile, provider: ProviderRecord) -> float:
        """Aligns project budget with manufacturer cost tier benchmark."""
        if not profile.budget_inr or profile.budget_inr <= 0:
            return 70.0  # Neutral score when budget is unstated

        budget_per_kw = profile.budget_inr / profile.target_capacity_kw
        expected_tier_cost = COST_TIER_BENCHMARKS.get(provider.estimated_cost_tier, 65000.0)

        pct_diff = abs(budget_per_kw - expected_tier_cost) / expected_tier_cost
        if pct_diff <= 0.20:
            return 100.0
        else:
            decay = max(40.0, 100.0 - (pct_diff * 100.0))
            return round(decay, 1)

    @classmethod
    def compute_missing_penalty(cls, provider: ProviderRecord) -> Tuple[float, List[str]]:
        """Identifies missing critical technical parameters and applies bounded penalty."""
        missing: List[str] = []
        if not provider.certifications:
            missing.append("No compliance certifications listed")
        if not provider.warranty_terms:
            missing.append("Detailed warranty terms unspecified")
        if not provider.in_country_warehouse:
            missing.append("No in-country spare parts warehouse")
        if not provider.pune_service_availability:
            missing.append("No verified Pune channel or service office")

        penalty = min(len(missing) * 5.0, 25.0)
        return penalty, missing

    @classmethod
    def score_provider(
        cls, profile: ProjectProfile, provider: ProviderRecord
    ) -> CompatibilityScore:
        """Calculates full compatibility score breakdown and qualitative tier."""
        weights = profile.priority_weights or DEFAULT_WEIGHTS

        # Normalize weights to sum to 1.0 if customized
        w_sum = sum(weights.values())
        w_norm = {k: v / w_sum for k, v in weights.items()}

        s_tech = cls.calculate_tech_fit(profile, provider)
        s_cap = cls.calculate_capacity_fit(profile, provider)
        s_svc = cls.calculate_service_fit(profile, provider)
        s_cert = cls.calculate_cert_fit(provider)
        s_doc = cls.calculate_doc_fit(provider)
        s_cost = cls.calculate_cost_fit(profile, provider)

        penalty, _ = cls.compute_missing_penalty(provider)

        weighted_total = (
            (w_norm.get("tech", 0.25) * s_tech)
            + (w_norm.get("capacity", 0.20) * s_cap)
            + (w_norm.get("service", 0.20) * s_svc)
            + (w_norm.get("cert", 0.15) * s_cert)
            + (w_norm.get("doc", 0.10) * s_doc)
            + (w_norm.get("cost", 0.10) * s_cost)
        )

        final_score = max(0.0, min(round(weighted_total - penalty, 1), 100.0))

        if final_score >= 85.0:
            tier = "Exceptional Match"
        elif final_score >= 70.0:
            tier = "Strong Match"
        elif final_score >= 50.0:
            tier = "Moderate Match"
        else:
            tier = "Low / Marginal Match"

        return CompatibilityScore(
            total_score=final_score,
            tech_fit=s_tech,
            capacity_fit=s_cap,
            service_fit=s_svc,
            cert_fit=s_cert,
            doc_fit=s_doc,
            cost_fit=s_cost,
            missing_penalty=penalty,
            score_tier=tier,
        )
