"""
Main Streamlit application entry point for the International Solar Technology Partner Matching Agent.
Targeted at rooftop solar installations in Pune City, Maharashtra, India.
Aligned with UN Sustainable Development Goal 7, Target 7.A.
"""

import json
import uuid
import pandas as pd
import streamlit as st
from config.settings import get_settings
from database.seed_db import seed_database
from src.data.provider_repository import SQLiteProviderRepository
from src.domain.models import (
    ProjectProfile,
    BuildingType,
    RoofType,
    TechType,
    GridCoupling,
    ServiceLevel,
)
from src.services.requirement_analyzer import RequirementAnalyzerService
from src.services.matching_service import MatchingService
from src.services.agent_workflow import MatchingAgentWorkflow
from src.llm import OpenRouterAdapter, GeminiAdapter, HuggingFaceAdapter, FallbackOrchestrator
from src.reports.report_generator import RecommendationReportService
from src.ui.components import (
    render_analysis_metrics,
    render_match_card,
    render_disqualified_card,
    render_zero_match_state,
)
from src.utils.logger import logger


# Page Configuration
st.set_page_config(
    page_title="Pune Rooftop Solar Partner Matching Agent (SDG 7.A)",
    page_icon="☀️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern, premium visual design
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    .main-header {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
        padding: 24px;
        border-radius: 12px;
        color: #F8FAFC;
        margin-bottom: 24px;
        border-bottom: 4px solid #10B981;
    }
    .sdg-badge {
        background: #10B98125;
        border: 1px solid #10B981;
        color: #10B981;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.85rem;
        font-weight: 600;
        display: inline-block;
        margin-bottom: 8px;
    }
    .stMetric {
        background-color: #F8FAFC;
        padding: 12px 16px;
        border-radius: 8px;
        border: 1px solid #E2E8F0;
    }
    </style>
    """,
    unsafe_allow_html=True
)

settings = get_settings()

# Initialize Database Repository
if not settings.absolute_db_path.exists():
    seed_database()

repo = SQLiteProviderRepository(settings.absolute_db_path)

# Initialize LLM Gateway with configured adapters
openrouter_adapter = OpenRouterAdapter(api_key=settings.openrouter_api_key, model_id=settings.openrouter_model)
gemini_adapter = GeminiAdapter(api_key=settings.gemini_api_key, model_id=settings.gemini_model)
hf_adapter = HuggingFaceAdapter(api_key=settings.huggingface_api_key, model_id=settings.huggingface_model)

orchestrator = FallbackOrchestrator(
    adapters=[openrouter_adapter, gemini_adapter, hf_adapter],
    max_retries=settings.llm_max_retries,
    backoff_base=settings.llm_backoff_base_seconds,
    default_timeout=settings.llm_timeout_seconds,
)

workflow = MatchingAgentWorkflow(repository=repo, orchestrator=orchestrator)


# Pre-defined realistic Pune scenarios
PUNE_SCENARIOS = {
    "— Select a Scenario or Enter Custom —": None,
    "Scenario 1: Kothrud Housing Society (35 kW Net-Metered)": {
        "name": "Kothrud Cooperative Housing Society Rooftop",
        "locality": "Kothrud, Pune",
        "building": BuildingType.HOUSING_SOCIETY,
        "capacity": 35.0,
        "budget": 2200000.0,
        "roof": RoofType.RCC_FLAT,
        "techs": [TechType.STRING_INVERTER, TechType.TOPCON],
        "grid": GridCoupling.ON_GRID_NET_METERED,
        "service": ServiceLevel.MAHARASHTRA_SERVICE_NETWORK,
    },
    "Scenario 2: Baner Residential Bungalow (6 kW Microinverter)": {
        "name": "Baner Individual Bungalow Solar",
        "locality": "Baner, Pune",
        "building": BuildingType.RESIDENTIAL_INDIVIDUAL,
        "capacity": 6.0,
        "budget": 450000.0,
        "roof": RoofType.RCC_FLAT,
        "techs": [TechType.MICROINVERTER, TechType.MONO_PERC],
        "grid": GridCoupling.ON_GRID_NET_METERED,
        "service": ServiceLevel.LOCAL_PUNE_OFFICE,
    },
    "Scenario 3: Hinjawadi Commercial IT Tech Park (150 kW)": {
        "name": "Hinjawadi IT Park Commercial Rooftop",
        "locality": "Hinjawadi Phase 1, PCMC",
        "building": BuildingType.COMMERCIAL,
        "capacity": 150.0,
        "budget": 9500000.0,
        "roof": RoofType.METAL_SHED,
        "techs": [TechType.STRING_INVERTER, TechType.TOPCON],
        "grid": GridCoupling.ON_GRID_NET_METERED,
        "service": ServiceLevel.MAHARASHTRA_SERVICE_NETWORK,
    },
}


def render_sidebar():
    """Renders the sidebar navigation, system health status, and weight tuning."""
    st.sidebar.markdown(
        """
        <div style="text-align: center; margin-bottom: 12px;">
            <h2 style="margin: 0; color: #10B981;">☀️ SolarMatch</h2>
            <p style="margin: 0; color: #64748B; font-size: 0.85rem;">Pune City Rooftop Solar Partner Agent</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.sidebar.markdown("---")

    # Knowledge Base Filter Control
    st.sidebar.subheader("📚 Provider Registry Filter")
    include_sample = st.sidebar.checkbox(
        "Include Synthetic Sample Fixtures",
        value=False,
        help="When unchecked, only authentic verified international providers are queried."
    )


    st.sidebar.markdown("---")
    # Advanced Multi-Criteria Weight Tuning
    with st.sidebar.expander("⚙️ Criteria Weights Configuration"):
        w_tech = st.slider("Technology Fit Weight", 0.0, 0.5, 0.25, 0.05)
        w_cap = st.slider("Operating Scale Weight", 0.0, 0.5, 0.20, 0.05)
        w_svc = st.slider("Service Footprint Weight", 0.0, 0.5, 0.20, 0.05)
        w_cert = st.slider("Certifications Weight", 0.0, 0.5, 0.15, 0.05)
        w_doc = st.slider("Documentation Depth Weight", 0.0, 0.5, 0.10, 0.05)
        w_cost = st.slider("Budget Feasibility Weight", 0.0, 0.5, 0.10, 0.05)

    custom_weights = {
        "tech": w_tech,
        "capacity": w_cap,
        "service": w_svc,
        "cert": w_cert,
        "doc": w_doc,
        "cost": w_cost,
    }

    return include_sample, custom_weights


def main():
    include_sample, custom_weights = render_sidebar()

    # Main Header
    st.markdown(
        """
        <div class="main-header">
            <span class="sdg-badge">UN SDG 7.A Clean Energy International Cooperation</span>
            <h1 style="margin: 6px 0 8px 0; font-size: 1.9rem;">
                International Solar Technology Partner Matching Agent
            </h1>
            <p style="margin: 0; color: #94A3B8; font-size: 1.05rem;">
                Connecting Pune City rooftop solar initiatives with verified, capable international equipment manufacturers,
                inverter topologies, and technical partners under MSEDCL net-metering standards.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    tab_intake, tab_matches, tab_reports, tab_catalog, tab_overview = st.tabs([
        "🏗️ Project Intake & Screening",
        "🎯 Matching Results & Rankings",
        "📑 Collaboration Report & Export",
        "📚 Provider Knowledge Base",
        "📋 Pune Context & Methodology"
    ])

    # --- TAB 1: PROJECT INTAKE ---
    with tab_intake:
        st.markdown("### 📝 Enter Project Requirements")

        # Scenario Preset Selector
        selected_scenario_key = st.selectbox(
            "Load a Pre-Configured Realistic Pune Scenario (Optional):",
            list(PUNE_SCENARIOS.keys())
        )
        scenario = PUNE_SCENARIOS[selected_scenario_key]

        with st.form("project_intake_form"):
            col1, col2 = st.columns(2)
            with col1:
                project_name = st.text_input(
                    "Project Title / Name *",
                    value=scenario["name"] if scenario else "Kothrud Society Common Area Solar",
                    help="Descriptive name of the rooftop installation project."
                )
                pune_locality = st.text_input(
                    "Pune Locality / Area *",
                    value=scenario["locality"] if scenario else "Kothrud, Pune",
                    help="Neighborhood in Pune or PCMC (e.g., Kothrud, Baner, Hinjawadi, PCMC, Hadapsar)."
                )
                building_type_idx = (
                    list(BuildingType).index(scenario["building"]) if scenario else 1
                )
                building_type = st.selectbox(
                    "Building Sector Type *",
                    list(BuildingType),
                    index=building_type_idx,
                    format_func=lambda x: x.value.replace("_", " ").title()
                )
                target_capacity_kw = st.number_input(
                    "Target Capacity (kW) *",
                    min_value=0.5,
                    max_value=2500.0,
                    value=float(scenario["capacity"]) if scenario else 35.0,
                    step=1.0,
                    help="Target rooftop solar DC capacity in kilowatts."
                )

            with col2:
                roof_type_idx = (
                    list(RoofType).index(scenario["roof"]) if scenario else 0
                )
                roof_type = st.selectbox(
                    "Roof Structural Type *",
                    list(RoofType),
                    index=roof_type_idx,
                    format_func=lambda x: x.value.replace("_", " ").title()
                )
                budget_inr = st.number_input(
                    "Estimated Total Budget (INR) (Optional)",
                    min_value=0.0,
                    max_value=500000000.0,
                    value=float(scenario["budget"]) if scenario else 2200000.0,
                    step=50000.0,
                    help="Total allocated capital expenditure in Indian Rupees."
                )
                grid_coupling_idx = (
                    list(GridCoupling).index(scenario["grid"]) if scenario else 0
                )
                grid_coupling = st.selectbox(
                    "Grid Interconnection Topology *",
                    list(GridCoupling),
                    index=grid_coupling_idx,
                    format_func=lambda x: x.value.replace("_", " ").title()
                )
                service_requirement_idx = (
                    list(ServiceLevel).index(scenario["service"]) if scenario else 1
                )
                service_requirement = st.selectbox(
                    "Minimum Local Service Support Level *",
                    list(ServiceLevel),
                    index=service_requirement_idx,
                    format_func=lambda x: x.value.replace("_", " ").title()
                )

            st.markdown("##### ⚙️ Desired Technology Components *")
            tech_options = list(TechType)
            default_techs = scenario["techs"] if scenario else [TechType.STRING_INVERTER, TechType.TOPCON]
            selected_techs = st.multiselect(
                "Select one or more technologies:",
                options=tech_options,
                default=default_techs,
                format_func=lambda x: x.value.replace("_", " ")
            )

            submit_button = st.form_submit_button("🚀 Run AI Matching & Partner Evaluation", type="primary")

        if submit_button:
            if not selected_techs:
                st.error("❌ Please select at least one desired technology component.")
            elif not project_name.strip() or not pune_locality.strip():
                st.error("❌ Project name and Pune locality cannot be empty.")
            else:
                try:
                    profile = ProjectProfile(
                        project_id=f"proj_{uuid.uuid4().hex[:8]}",
                        project_name=project_name.strip(),
                        pune_locality=pune_locality.strip(),
                        building_type=building_type,
                        target_capacity_kw=float(target_capacity_kw),
                        budget_inr=float(budget_inr) if budget_inr > 0 else None,
                        roof_type=roof_type,
                        technology_preference=selected_techs,
                        grid_coupling=grid_coupling,
                        service_requirement=service_requirement,
                        priority_weights=custom_weights,
                    )

                    with st.spinner("🤖 AI Agent is evaluating technical compatibility and generating strategic partner synthesis via Meta LLaMA 3.1..."):
                        wf_res = workflow.run_workflow(
                            profile=profile,
                            include_sample=include_sample,
                            trigger_llm_synthesis=True,
                        )

                    st.session_state["active_profile"] = profile
                    st.session_state["wf_result"] = wf_res
                    st.session_state["eligible_results"] = wf_res.eligible_results
                    st.session_state["disqualified_results"] = wf_res.disqualified_results
                    st.session_state["analysis"] = wf_res.analysis
                    st.session_state["current_md_report"] = wf_res.markdown_report
                    st.session_state["current_json_report"] = json.dumps(wf_res.json_report, indent=2)

                    st.success(f"✅ AI Matching and Synthesis completed for **{profile.project_name}**! Switch to 'Matching Results' or view summary below.")
                except Exception as e:
                    st.error(f"❌ Input Validation Error: {str(e)}")

        # Immediate AI Output Card on Tab 1
        if "wf_result" in st.session_state and st.session_state["wf_result"]:
            wf = st.session_state["wf_result"]
            top_p = wf.eligible_results[0].provider.name if wf.eligible_results else "None"
            top_s = f"{wf.eligible_results[0].compatibility_score.total_score:.1f}" if wf.eligible_results else "N/A"
            st.markdown("---")
            st.markdown(
                f"""
                <div style="border: 2px solid #10B981; border-radius: 10px; padding: 18px; background: #F0FDF4; margin-top: 15px;">
                    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px;">
                        <h4 style="margin: 0; color: #065F46;">🤖 Live AI Agent Output ({wf.profile.project_name})</h4>
                        <span style="background: #10B981; color: white; padding: 3px 10px; border-radius: 20px; font-size: 0.8rem; font-weight: 600;">Top Match: {top_p} ({top_s}/100)</span>
                    </div>
                    <p style="margin: 0 0 10px 0; color: #1F2937; line-height: 1.6; font-size: 0.95rem;">
                        {wf.executive_synthesis if wf.executive_synthesis else 'Screening completed with verified international partners.'}
                    </p>
                    <small style="color: #64748B;">⚡ Model: <b>Meta LLaMA 3.1 8B Instruct</b> via OpenRouter | Evaluated: <b>{len(wf.eligible_results) + len(wf.disqualified_results)} candidates</b> (100% verified genuine providers)</small>
                </div>
                """,
                unsafe_allow_html=True
            )

    # --- TAB 2: MATCHING RESULTS ---
    with tab_matches:
        if "active_profile" not in st.session_state:
            st.info("👈 Please define and submit a project profile in the **Project Intake** tab to view partner matches.")
        else:
            profile: ProjectProfile = st.session_state["active_profile"]
            eligible: list = st.session_state.get("eligible_results", [])
            disqualified: list = st.session_state.get("disqualified_results", [])
            analysis: dict = st.session_state.get("analysis", {})
            wf_res = st.session_state.get("wf_result")

            st.markdown(f"### Screening Results: *{profile.project_name}*")
            st.caption(f"📍 {profile.pune_locality} | 🏢 {profile.building_type.value} | ⚡ {profile.target_capacity_kw} kW")

            # Prominent Live AI Strategic Briefing
            synth_text = wf_res.executive_synthesis if wf_res and wf_res.executive_synthesis else ""
            if not synth_text and wf_res and wf_res.markdown_report:
                try:
                    synth_text = wf_res.markdown_report.split("## 2.")[0].split("## 1. Executive Summary")[-1].strip()
                except Exception:
                    synth_text = ""
            if synth_text:
                st.markdown(
                    f"""
                    <div style="
                        border: 1px solid #10B981;
                        border-left: 6px solid #10B981;
                        border-radius: 8px;
                        padding: 16px 20px;
                        margin-bottom: 24px;
                        background-color: #ECFDF5;
                    ">
                        <h4 style="margin: 0 0 8px 0; color: #065F46;">🤖 Live AI Agent Recommendation (Meta LLaMA 3.1 via OpenRouter)</h4>
                        <p style="margin: 0; color: #1F2937; line-height: 1.6; font-size: 0.95rem;">{synth_text}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            # Technical Analysis KPI cards
            render_analysis_metrics(analysis)
            st.markdown("---")

            col_summary1, col_summary2 = st.columns(2)
            with col_summary1:
                st.markdown(f"#### 🏆 Qualified Technology Partners ({len(eligible)})")
            with col_summary2:
                st.markdown(f"#### 🚫 Disqualified Providers ({len(disqualified)})")

            if not eligible:
                render_zero_match_state()
            else:
                for idx, result in enumerate(eligible, 1):
                    render_match_card(result, rank=idx)

            if disqualified:
                with st.expander(f"View Disqualified Providers ({len(disqualified)})"):
                    for result in disqualified:
                        render_disqualified_card(result)

    # --- TAB 3: COLLABORATION REPORT & EXPORT ---
    with tab_reports:
        if "active_profile" not in st.session_state:
            st.info("👈 Please define and run a project screening in the **Project Intake** tab first.")
        else:
            profile: ProjectProfile = st.session_state["active_profile"]
            eligible: list = st.session_state.get("eligible_results", [])
            disqualified: list = st.session_state.get("disqualified_results", [])
            analysis: dict = st.session_state.get("analysis", {})

            st.markdown(f"### 📑 UN SDG 7.A Collaboration Recommendation Report")
            st.caption(f"Project: **{profile.project_name}** | Target: {profile.target_capacity_kw} kW | Locality: {profile.pune_locality}")

            col_rep_btn1, col_rep_btn2 = st.columns([1, 1])
            with col_rep_btn1:
                gen_llm = st.button("🤖 Generate / Refresh with LLM Synthesis", help="Calls configured LLM gateway (or offline deterministic fallback) to generate natural language summary.")
            
            # Check or generate report
            if gen_llm or "current_md_report" not in st.session_state:
                with st.spinner("Compiling evidence-grounded recommendation report..."):
                    wf_res = workflow.run_workflow(
                        profile=profile,
                        include_sample=include_sample,
                        trigger_llm_synthesis=gen_llm,
                    )
                    st.session_state["current_md_report"] = wf_res.markdown_report
                    st.session_state["current_json_report"] = json.dumps(wf_res.json_report, indent=2)

            md_content = st.session_state.get("current_md_report", "")
            json_content = st.session_state.get("current_json_report", "{}")

            # Download Buttons
            st.markdown("#### 💾 Export Report")
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                st.download_button(
                    label="📥 Download Markdown Report (.md)",
                    data=md_content,
                    file_name=f"SolarMatch_Report_{profile.project_name.replace(' ', '_')}.md",
                    mime="text/markdown",
                    type="primary",
                )
            with col_d2:
                st.download_button(
                    label="📥 Download Structured JSON Data (.json)",
                    data=json_content,
                    file_name=f"SolarMatch_Data_{profile.project_name.replace(' ', '_')}.json",
                    mime="application/json",
                )

            st.markdown("---")
            st.markdown("#### 📄 Document Preview")
            with st.expander("View Full Report Markdown Preview", expanded=True):
                st.markdown(md_content)

    # --- TAB 4: PROVIDER KNOWLEDGE BASE EXPLORER ---
    with tab_catalog:
        st.markdown("### 📚 International Solar Technology Knowledge Base")
        st.markdown(
            "Curated international equipment manufacturers, inverter topologies, and battery storage providers "
            "with verified presence and authorized channel partners in India."
        )

        all_providers = repo.list_providers(include_sample=include_sample)
        if all_providers:
            table_data = []
            for p in all_providers:
                table_data.append({
                    "Provider Name": p.name,
                    "Country": p.headquarters_country,
                    "Technologies": ", ".join([t.value for t in p.primary_technologies]),
                    "Capacity Range": f"{p.min_capacity_kw:.1f} - {p.max_capacity_kw:.0f} kW",
                    "India Presence": p.india_presence_type.value,
                    "Pune Office": "✅ Yes" if p.pune_service_availability else "❌ No",
                    "Warehouse": "✅ Yes" if p.in_country_warehouse else "❌ No",
                    "Cost Tier": p.estimated_cost_tier.value,
                    "Type": "Synthetic Sample" if p.is_sample_data else "Verified Genuine",
                })
            df = pd.DataFrame(table_data)
            st.dataframe(df, width="stretch")

            st.markdown("---")
            st.markdown("#### 🔍 Provider Evidence Citations")
            selected_provider_name = st.selectbox(
                "Inspect authenticated source citations for a provider:",
                [p.name for p in all_providers]
            )
            selected_provider = next(p for p in all_providers if p.name == selected_provider_name)

            st.markdown(f"**Entity:** {selected_provider.name} ({selected_provider.headquarters_country})")
            st.markdown(f"**Certifications:** `{', '.join(selected_provider.certifications)}`")
            st.markdown(f"**Warranty Terms:** `{selected_provider.warranty_terms}`")
            st.markdown(f"**Last Audit Date:** `{selected_provider.last_audit_date}`")

            for ev in selected_provider.evidence_records:
                st.markdown(
                    f"- **Claim:** {ev.claim}  \n"
                    f"  🔗 **Source:** [{ev.source_url}]({ev.source_url}) ({ev.source_type.value})  \n"
                    f"  📅 Verified: `{ev.last_verified}` | *{ev.verification_note}*"
                )

    # --- TAB 4: PUNE CONTEXT & METHODOLOGY ---
    with tab_overview:
        st.markdown("### 📋 Pune City Rooftop Solar Guidelines & Methodology")
        st.markdown(
            """
            #### 1. Geographic & Climatic Context
            Pune experiences tropical wet-and-dry climatic conditions with high summer irradiation (~5.5 kWh/m²/day),
            heavy monsoon clouding (June–September), and significant dust/soiling accumulation. Equipment selection
            must prioritize:
            - High-temperature coefficient modules (e.g., TOPCon or HJT) to minimize heat degradation.
            - Reliable ingress protection (IP65 / IP66) for inverters during monsoon downpours.
            - Rapid shutdown and module-level monitoring for complex housing society roofs.

            #### 2. MSEDCL Net-Metering Regulations
            - Rooftop solar installations are governed under the **Maharashtra Electricity Regulatory Commission (MERC) Net Metering Regulations**.
            - Interconnection capacity is capped at 100% of the consumer's sanctioned load / contract demand.
            - Housing Societies require dedicated common-service meters and General Body Meeting (GBM) resolutions.

            #### 3. Matching Methodology
            - **Stage 1 (Hard Filtering):** Strict elimination based on technology availability, capacity feasibility, and local service support requirements.
            - **Stage 2 (Compatibility Scoring):** Transparent, deterministic scoring:
            $$\\text{Score} = (0.25 \\cdot s_{\\text{tech}}) + (0.20 \\cdot s_{\\text{cap}}) + (0.20 \\cdot s_{\\text{svc}}) + (0.15 \\cdot s_{\\text{cert}}) + (0.10 \\cdot s_{\\text{doc}}) + (0.10 \\cdot s_{\\text{cost}}) - P_{\\text{missing}}$$
            """
        )


if __name__ == "__main__":
    main()
