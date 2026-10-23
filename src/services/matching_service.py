"""
Matching Service Orchestrator.
Combines requirement analysis, hard eligibility filtering, deterministic compatibility scoring,
explanation synthesis, and ranking into a unified pipeline.
"""

from typing import List, Tuple
from src.domain.models import ProjectProfile, ProviderRecord, MatchResult
from src.services.provider_search import ProviderSearchService
from src.services.compatibility_scorer import CompatibilityScoringService
from src.services.explanation_service import ExplanationService
from src.utils.logger import logger


class MatchingService:
    """Coordinates deterministic two-stage matching and ranking of international solar partners."""

    @classmethod
    def match_providers(
        cls, profile: ProjectProfile, candidates: List[ProviderRecord]
    ) -> Tuple[List[MatchResult], List[MatchResult]]:
        """
        Evaluates all candidate providers against the project profile.
        Returns:
            (ranked_eligible_results, disqualified_results)
        """
        logger.info(
            "Evaluating %d candidates for project '%s' (Capacity: %.1f kW, Building: %s)",
            len(candidates), profile.project_name, profile.target_capacity_kw, profile.building_type.value
        )

        eligible_results: List[MatchResult] = []
        disqualified_results: List[MatchResult] = []

        for provider in candidates:
            is_eligible, disqualification_reasons = ProviderSearchService.evaluate_eligibility(
                profile, provider
            )

            if is_eligible:
                score = CompatibilityScoringService.score_provider(profile, provider)
                drivers, risks, missing = ExplanationService.generate_explanations(
                    profile, provider, score
                )
                match_res = MatchResult(
                    provider=provider,
                    is_eligible=True,
                    disqualification_reasons=[],
                    compatibility_score=score,
                    positive_drivers=drivers,
                    risk_flags=risks,
                    missing_fields=missing,
                )
                eligible_results.append(match_res)
            else:
                match_res = MatchResult(
                    provider=provider,
                    is_eligible=False,
                    disqualification_reasons=disqualification_reasons,
                    compatibility_score=None,
                    positive_drivers=[],
                    risk_flags=[],
                    missing_fields=[],
                )
                disqualified_results.append(match_res)

        # Sort eligible providers by total_score in descending order
        eligible_results.sort(
            key=lambda m: m.compatibility_score.total_score if m.compatibility_score else 0.0,
            reverse=True,
        )

        logger.info(
            "Matching complete: %d eligible (Top score: %.1f), %d disqualified",
            len(eligible_results),
            eligible_results[0].compatibility_score.total_score if eligible_results else 0.0,
            len(disqualified_results),
        )

        return eligible_results, disqualified_results
