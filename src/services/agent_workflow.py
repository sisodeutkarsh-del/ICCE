"""
Unified Matching Agent Workflow.
Connects requirement analysis, provider querying, two-stage deterministic scoring,
optional resilient LLM synthesis, and evidence-grounded report generation.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from src.domain.models import ProjectProfile, MatchResult
from src.data.provider_repository import SQLiteProviderRepository
from src.services.requirement_analyzer import RequirementAnalyzerService
from src.services.matching_service import MatchingService
from src.llm.fallback_orchestrator import FallbackOrchestrator
from src.reports.report_generator import RecommendationReportService
from src.utils.logger import logger


class AgentWorkflowResult(BaseModel):
    """Encapsulates the complete result of an end-to-end matching run."""
    profile: ProjectProfile
    analysis: Dict[str, Any]
    eligible_results: List[MatchResult]
    disqualified_results: List[MatchResult]
    executive_synthesis: str
    markdown_report: str
    json_report: Dict[str, Any]
    llm_telemetry: Optional[Dict[str, Any]] = None



class MatchingAgentWorkflow:
    """End-to-end autonomous agent workflow for international solar partner matching."""

    def __init__(
        self,
        repository: SQLiteProviderRepository,
        orchestrator: Optional[FallbackOrchestrator] = None,
    ):
        self.repository = repository
        self.orchestrator = orchestrator

    def run_workflow(
        self,
        profile: ProjectProfile,
        include_sample: bool = False,
        trigger_llm_synthesis: bool = True,
    ) -> AgentWorkflowResult:
        """Executes the full pipeline from intake to final report."""
        logger.info("Executing MatchingAgentWorkflow for project '%s'", profile.project_name)

        # 1. Technical sizing analysis
        analysis = RequirementAnalyzerService.analyze_project(profile)

        # 2. Retrieve candidate providers from repository
        candidates = self.repository.list_providers(include_sample=include_sample)

        # 3. Two-stage deterministic matching
        eligible, disqualified = MatchingService.match_providers(profile, candidates)

        # 4. Optional resilient LLM executive synthesis
        synthesis = ""
        telemetry = None
        if trigger_llm_synthesis and self.orchestrator:
            try:
                top_3 = [
                    f"{r.provider.name} ({r.provider.headquarters_country}) - Score: {r.compatibility_score.total_score:.1f}"
                    for r in eligible[:3]
                ]
                prompt = (
                    f"Synthesize a professional 3-sentence executive summary for rooftop solar partner matching in Pune City.\n"
                    f"Project: {profile.project_name} in {profile.pune_locality}.\n"
                    f"Target Capacity: {profile.target_capacity_kw} kW. Building: {profile.building_type.value}.\n"
                    f"Top Matched Partners: {', '.join(top_3) if top_3 else 'None'}.\n"
                    f"Emphasize local service presence in Maharashtra and UN SDG 7.A cooperation."
                )
                system_prompt = (
                    "You are the senior solar technology advisor for Pune City municipal rooftop installations. "
                    "Provide factual, evidence-grounded insights without promotional fluff."
                )
                logger.info("Calling LLM Gateway via FallbackOrchestrator for project '%s'...", profile.project_name)
                llm_res = self.orchestrator.generate_with_fallback(prompt, system_prompt=system_prompt)
                synthesis = llm_res.content
                telemetry = {
                    "provider_name": llm_res.provider_name,
                    "model_id": llm_res.model_id,
                    "latency_seconds": round(llm_res.latency_seconds, 2),
                    "token_usage": llm_res.token_usage or {},
                    "prompt_sent": prompt,
                    "system_prompt": system_prompt,
                    "is_fallback": llm_res.is_fallback,
                }
                logger.info(
                    "Live AI synthesis received from provider '%s' (model: %s) in %.2fs",
                    llm_res.provider_name,
                    llm_res.model_id,
                    llm_res.latency_seconds,
                )
            except Exception as e:
                logger.warning("LLM synthesis failed; proceeding with template synthesis: %s", str(e))
                if not synthesis:
                    synthesis = ""

        # 5. Generate Markdown and JSON reports
        md_report = RecommendationReportService.generate_markdown_report(
            profile=profile,
            analysis=analysis,
            eligible_results=eligible,
            disqualified_results=disqualified,
            llm_synthesis=synthesis if synthesis else None,
        )

        json_report = RecommendationReportService.generate_json_report(
            profile=profile,
            analysis=analysis,
            eligible_results=eligible,
            disqualified_results=disqualified,
            llm_synthesis=synthesis if synthesis else None,
        )

        logger.info(
            "Agent workflow completed successfully for '%s'. Report length: %d chars",
            profile.project_name, len(md_report)
        )

        return AgentWorkflowResult(
            profile=profile,
            analysis=analysis,
            eligible_results=eligible,
            disqualified_results=disqualified,
            executive_synthesis=synthesis,
            markdown_report=md_report,
            json_report=json_report,
            llm_telemetry=telemetry,
        )
