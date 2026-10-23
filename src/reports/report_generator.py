"""
Recommendation Report Generator Service.
Synthesizes comprehensive, evidence-grounded Collaboration Recommendation Reports
aligned with UN SDG 7.A and Pune MSEDCL regulatory standards in Markdown and JSON formats.
"""

from datetime import datetime
import json
from typing import Any, Dict, List, Optional
from src.domain.models import ProjectProfile, MatchResult


DISCLAIMER_TEXT = """
> [!IMPORTANT]
> **DISCLAIMER & REGULATORY NOTICE:**
> 1. This report is an AI-assisted technical partner compatibility screening prepared for academic and preliminary planning purposes under UN Sustainable Development Goal 7, Target 7.A.
> 2. It does not constitute a formal structural audit, electrical engineering sign-off, commercial tender, or financial investment advice.
> 3. Final rooftop structural load bearing capacity, shadow analysis, electrical sanction from MSEDCL (Maharashtra State Electricity Distribution Company Limited), and MNRE subsidy compliance must be certified by a licensed Electrical Contractor / Solar EPC in Pune.
"""


class RecommendationReportService:
    """Generates structured Markdown and JSON reports from matching results."""

    @classmethod
    def generate_markdown_report(
        cls,
        profile: ProjectProfile,
        analysis: Dict[str, Any],
        eligible_results: List[MatchResult],
        disqualified_results: List[MatchResult],
        llm_synthesis: Optional[str] = None,
    ) -> str:
        """Constructs an evidence-grounded Markdown collaboration report."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        md = []
        md.append("# ☀️ INTERNATIONAL SOLAR TECHNOLOGY PARTNER MATCHING REPORT")
        md.append(f"**Project Name:** {profile.project_name}  ")
        md.append(f"**Target Geography:** {profile.pune_locality}, Maharashtra, India  ")
        md.append(f"**Date Generated:** {timestamp}  ")
        md.append(f"**UN SDG Alignment:** Goal 7, Target 7.A (Clean Energy Technology & Investment Cooperation)  ")
        md.append("\n---\n")

        # 1. Executive Summary
        md.append("## 1. Executive Summary")
        if llm_synthesis:
            md.append(llm_synthesis)
        else:
            top_provider = eligible_results[0].provider.name if eligible_results else "None"
            top_score = (
                f"{eligible_results[0].compatibility_score.total_score:.1f}/100"
                if eligible_results and eligible_results[0].compatibility_score
                else "N/A"
            )
            md.append(
                f"A deterministic screening was conducted for a **{profile.target_capacity_kw:.1f} kW** "
                f"rooftop solar PV installation in **{profile.pune_locality}** ({profile.building_type.value.replace('_', ' ').title()}). "
                f"Out of **{len(eligible_results) + len(disqualified_results)}** international technology candidates, "
                f"**{len(eligible_results)}** passed Stage 1 hard eligibility gates. "
                f"The highest-ranked partner is **{top_provider}** with a compatibility score of **{top_score}**."
            )
        md.append("\n")

        # 2. Pune Engineering Sizing & Benchmarks
        md.append("## 2. Pune Rooftop Sizing & Energy Yield Projection")
        md.append(f"- **Target Solar Capacity:** {profile.target_capacity_kw:.1f} kW")
        md.append(f"- **Estimated Annual Solar Generation:** {analysis.get('estimated_annual_generation_kwh', 0):,.0f} kWh/year (at 1,500 kWh/kWp/year)")
        md.append(f"- **Estimated Rooftop Surface Required:** {analysis.get('estimated_roof_area_sqft', 0):,.0f} sq.ft (~{analysis.get('estimated_roof_area_sqm', 0):,.0f} m²)")
        md.append(f"- **Estimated Annual CO₂ Emission Offset:** {analysis.get('estimated_co2_offset_tons_per_year', 0):.1f} metric tons/year")
        if profile.budget_inr:
            budget_per_kw = profile.budget_inr / profile.target_capacity_kw
            md.append(f"- **Allocated Capital Budget:** ₹{profile.budget_inr:,.0f} (₹{budget_per_kw:,.0f}/kW)")

        if analysis.get("regulatory_notes"):
            md.append("\n### Pune MSEDCL Grid Interconnection Standards:")
            for note in analysis["regulatory_notes"]:
                md.append(f"- {note}")
        md.append("\n")

        # 3. Ranked Technology Partner Recommendations
        md.append("## 3. Ranked International Technology Partner Recommendations")
        if not eligible_results:
            md.append("*(No international providers met all Stage 1 hard eligibility gates for this specific configuration.)*\n")
        else:
            for idx, res in enumerate(eligible_results, 1):
                p = res.provider
                s = res.compatibility_score
                md.append(f"### #{idx}. {p.name} ({p.headquarters_country})")
                md.append(f"**Overall Compatibility Score:** **{s.total_score:.1f} / 100** (`{s.score_tier}`)")
                md.append(
                    f"- **Score Breakdown:** Tech Fit: {s.tech_fit:.0f}% | Operating Scale: {s.capacity_fit:.0f}% | "
                    f"Local Service: {s.service_fit:.0f}% | BIS/IEC: {s.cert_fit:.0f}% | Documentation: {s.doc_fit:.0f}%"
                )
                if s.missing_penalty > 0:
                    md.append(f"- **Unverified Data Penalty:** -{s.missing_penalty:.1f} pts")

                md.append(f"- **Presence Structure in India:** {p.india_presence_type.value}")
                md.append(f"- **Pune Channel / Service Office:** {'Verified Active' if p.pune_service_availability else 'Not Verified in Pune'}")
                md.append(f"- **In-Country Spare Parts Warehouse:** {'Verified Active' if p.in_country_warehouse else 'Not Verified'}")
                md.append(f"- **Compliance Certifications:** `{', '.join(p.certifications)}`")

                if res.positive_drivers:
                    md.append("- **Key Strategic Advantages:**")
                    for d in res.positive_drivers:
                        md.append(f"  - ✅ {d}")

                if res.risk_flags:
                    md.append("- **Identified Risks / Due-Diligence Caveats:**")
                    for r in res.risk_flags:
                        md.append(f"  - ⚠️ {r}")

                if res.missing_fields:
                    md.append("- **Unverified Technical Parameters:**")
                    for m in res.missing_fields:
                        md.append(f"  - ❓ {m}")

                # Verified evidence trail
                md.append("- **Authenticated Source Citations:**")
                for ev in p.evidence_records:
                    md.append(
                        f"  - *\"{ev.claim}\"* — [{ev.source_type.value}]({ev.source_url}) (Verified: {ev.last_verified})"
                    )
                md.append("\n")

        # 4. Disqualified Candidates
        if disqualified_results:
            md.append("## 4. Disqualified Provider Summary")
            md.append("| Provider Name | Country | Disqualification Reason(s) |")
            md.append("| :--- | :--- | :--- |")
            for res in disqualified_results:
                reasons_str = "; ".join(res.disqualification_reasons)
                md.append(f"| {res.provider.name} | {res.provider.headquarters_country} | {reasons_str} |")
            md.append("\n")

        # 5. UN SDG 7.A Impact Analysis
        md.append("## 5. UN Sustainable Development Goal 7.A Alignment")
        md.append(
            "This project facilitates direct international clean-energy technology transfer and partnership "
            "between international equipment manufacturers and local rooftop consumers in Pune. By grounding "
            "recommendations in verified datasheets and BIS compliance, this matching agent reduces information "
            "asymmetry and supports Pune's transition to decentralized urban solar power."
        )
        md.append("\n")

        # 6. Disclaimers
        md.append(DISCLAIMER_TEXT)

        return "\n".join(md)

    @classmethod
    def generate_json_report(
        cls,
        profile: ProjectProfile,
        analysis: Dict[str, Any],
        eligible_results: List[MatchResult],
        disqualified_results: List[MatchResult],
        llm_synthesis: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Constructs a serializable dictionary representation of the report."""
        return {
            "metadata": {
                "report_title": "International Solar Technology Partner Matching Report",
                "sdg_target": "UN SDG 7.A (Clean Energy Technology & Investment Cooperation)",
                "generated_at": datetime.now().isoformat(),
                "generator": "Pune Rooftop Solar Partner Matching Agent v1.0",
            },
            "project_profile": profile.model_dump(mode="json"),
            "technical_sizing_analysis": analysis,
            "executive_synthesis": llm_synthesis,
            "eligible_partners": [
                {
                    "rank": idx + 1,
                    "provider_id": res.provider.provider_id,
                    "provider_name": res.provider.name,
                    "country": res.provider.headquarters_country,
                    "compatibility_score": res.compatibility_score.model_dump(mode="json") if res.compatibility_score else None,
                    "positive_drivers": res.positive_drivers,
                    "risk_flags": res.risk_flags,
                    "missing_fields": res.missing_fields,
                    "evidence_citations": [ev.model_dump(mode="json") for ev in res.provider.evidence_records],
                }
                for idx, res in enumerate(eligible_results)
            ],
            "disqualified_providers": [
                {
                    "provider_id": res.provider.provider_id,
                    "provider_name": res.provider.name,
                    "country": res.provider.headquarters_country,
                    "reasons": res.disqualification_reasons,
                }
                for res in disqualified_results
            ],
            "disclaimer": DISCLAIMER_TEXT.strip(),
        }
