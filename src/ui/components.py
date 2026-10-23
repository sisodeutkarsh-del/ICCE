"""
UI Components and rendering helpers for the Streamlit web application.
Includes styling tokens, score badges, cards, metrics, and evidence viewers.
"""

from typing import Dict, List, Optional
import streamlit as st
from src.domain.models import MatchResult, ProviderRecord, BuildingType, TechType


# Color tokens for score tiers
TIER_COLORS = {
    "Exceptional Match": "#10B981",  # Emerald Green
    "Strong Match": "#3B82F6",       # Cobalt Blue
    "Moderate Match": "#F59E0B",     # Amber
    "Low / Marginal Match": "#EF4444" # Crimson Red
}


def get_tier_color(tier: str) -> str:
    """Returns hexadecimal color code for a qualitative score tier."""
    return TIER_COLORS.get(tier, "#6B7280")


def render_score_badge(score: float, tier: str) -> str:
    """Returns HTML snippet for a colored score badge."""
    color = get_tier_color(tier)
    return f"""
    <span style="
        background-color: {color}20;
        color: {color};
        border: 1px solid {color};
        padding: 4px 10px;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 0.9rem;
    ">
        ★ {score:.1f}/100 — {tier}
    </span>
    """


def render_analysis_metrics(analysis: Dict):
    """Renders high-level project requirement metrics and MSEDCL notes."""
    st.markdown("#### ⚡ Pune Technical Sizing & Energy Projection")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            label="Target Capacity",
            value=f"{analysis['target_capacity_kw']:.1f} kW"
        )
    with col2:
        st.metric(
            label="Annual Generation",
            value=f"{analysis['estimated_annual_generation_kwh']:,.0f} kWh/yr"
        )
    with col3:
        st.metric(
            label="Est. Roof Area",
            value=f"{analysis['estimated_roof_area_sqft']:,.0f} sq.ft"
        )
    with col4:
        st.metric(
            label="CO₂ Offset",
            value=f"{analysis['estimated_co2_offset_tons_per_year']:.1f} tons/yr"
        )

    if analysis.get("regulatory_notes"):
        with st.expander("📌 Pune MSEDCL Net-Metering & Regulatory Considerations", expanded=True):
            for note in analysis["regulatory_notes"]:
                st.markdown(f"- {note}")


def render_match_card(result: MatchResult, rank: int):
    """Renders a ranked partner recommendation card with score breakdown and evidence."""
    provider = result.provider
    score = result.compatibility_score

    tier_color = get_tier_color(score.score_tier) if score else "#6B7280"

    with st.container():
        st.markdown(
            f"""
            <div style="
                border: 1px solid #E5E7EB;
                border-left: 6px solid {tier_color};
                border-radius: 8px;
                padding: 16px 20px;
                margin-bottom: 20px;
                background-color: #FFFFFF;
                box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            ">
                <div style="display: flex; justify-content: space-between; align-items: baseline;">
                    <h3 style="margin: 0; color: #111827;">#{rank}. {provider.name}</h3>
                    <div>{render_score_badge(score.total_score, score.score_tier) if score else ""}</div>
                </div>
                <p style="margin: 4px 0 12px 0; color: #4B5563; font-size: 0.9rem;">
                    🌐 <b>Headquarters:</b> {provider.headquarters_country} | 
                    🏢 <b>India Presence:</b> {provider.india_presence_type.value} | 
                    📍 <b>Pune Local Office:</b> {'✅ Yes' if provider.pune_service_availability else '❌ No'} |
                    📦 <b>India Warehouse:</b> {'✅ Yes' if provider.in_country_warehouse else '❌ No'}
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

        col_scores, col_details = st.columns([1, 1])

        with col_scores:
            st.markdown("##### 📊 Compatibility Breakdown")
            st.write(f"**Technology Fit:** {score.tech_fit:.0f}%")
            st.progress(int(score.tech_fit))
            st.write(f"**Operating Scale Fit:** {score.capacity_fit:.0f}%")
            st.progress(int(score.capacity_fit))
            st.write(f"**India/Pune Service Footprint:** {score.service_fit:.0f}%")
            st.progress(int(score.service_fit))
            st.write(f"**BIS/IEC Compliance:** {score.cert_fit:.0f}%")
            st.progress(int(score.cert_fit))
            st.write(f"**Documentation Depth:** {score.doc_fit:.0f}%")
            st.progress(int(score.doc_fit))
            if score.missing_penalty > 0:
                st.caption(f"⚠️ **Missing Data Deduction:** -{score.missing_penalty:.1f} pts")

        with col_details:
            st.markdown("##### 💡 Justification & Evidence")
            if result.positive_drivers:
                st.markdown("**Key Advantages:**")
                for d in result.positive_drivers:
                    st.markdown(f"- ✅ {d}")

            if result.risk_flags:
                st.markdown("**Due-Diligence Caveats:**")
                for r in result.risk_flags:
                    st.markdown(f"- ⚠️ {r}")

            if result.missing_fields:
                st.markdown("**Unverified Parameters:**")
                for m in result.missing_fields:
                    st.markdown(f"- ❓ {m}")

        # Verified Evidence Inspector Expander
        with st.expander(f"🔍 Inspect Verified Citations ({len(provider.evidence_records)})"):
            for ev in provider.evidence_records:
                st.markdown(f"**Claim:** *\"{ev.claim}\"*")
                st.markdown(
                    f"🔗 **Source [{ev.source_type.value}]:** [{ev.source_url}]({ev.source_url})  \n"
                    f"📅 **Last Verified:** `{ev.last_verified}` | **Note:** {ev.verification_note or 'Audited'}"
                )
                st.divider()

        st.markdown("<br>", unsafe_allow_html=True)


def render_disqualified_card(result: MatchResult):
    """Renders a card for disqualified candidates with explicit gate rejection reasons."""
    provider = result.provider
    with st.container():
        st.markdown(
            f"""
            <div style="
                border: 1px dashed #D1D5DB;
                border-left: 4px solid #9CA3AF;
                border-radius: 6px;
                padding: 12px 16px;
                margin-bottom: 12px;
                background-color: #F9FAFB;
            ">
                <div style="display: flex; justify-content: space-between;">
                    <h4 style="margin: 0; color: #4B5563;">{provider.name} ({provider.headquarters_country})</h4>
                    <span style="color: #6B7280; font-size: 0.85rem; font-weight: 600;">DISQUALIFIED</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        for r in result.disqualification_reasons:
            st.markdown(f"- ❌ {r}")


def render_zero_match_state():
    """Renders helpful troubleshooting guidance when no providers meet the hard criteria."""
    st.warning("⚠️ **No international technology partners met all Stage 1 hard eligibility gates.**")
    st.markdown(
        """
        #### 💡 How to troubleshoot your criteria:
        1. **Broaden Technology Scope:** Some international inverter manufacturers do not manufacture PV modules directly, and vice versa. Consider evaluating inverter and module technologies in separate project queries.
        2. **Review Capacity Constraints:** Check if your target kW capacity is within typical residential (< 25 kW) or commercial (< 500 kW) bounds.
        3. **Relax Service Footprint:** If you required a local Pune office, try selecting **Pan-India Authorized Partner** to view reputable providers offering remote engineering support.
        """
    )
