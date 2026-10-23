"""
Main Streamlit application entry point for the International Solar Technology Partner Matching Agent.
Targeted at rooftop solar installations in Pune City, Maharashtra, India.
Aligned with UN Sustainable Development Goal 7, Target 7.A.
"""

import streamlit as st
from config.settings import get_settings
from src.utils.logger import logger

# Page configuration
st.set_page_config(
    page_title="Pune Rooftop Solar Partner Matching Agent (SDG 7.A)",
    page_icon="☀️",
    layout="wide",
    initial_sidebar_state="expanded"
)

settings = get_settings()
logger.info("Starting Streamlit application. Environment: %s", settings.app_env)


def render_sidebar():
    """Renders the global navigation and system status sidebar."""
    st.sidebar.image("https://raw.githubusercontent.com/sisodeutkarsh-del/ICCE/main/docs/assets/sdg7_badge.png", width=120) if False else None
    st.sidebar.title("☀️ Solar Match Pune")
    st.sidebar.caption("UN SDG 7.A Clean Energy Technology Matching")
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔌 System Health & Adapters")
    
    # Provider key status with masked keys
    st.sidebar.markdown(f"**OpenRouter:** `{settings.masked_key('openrouter_api_key')}`")
    st.sidebar.markdown(f"**HuggingFace:** `{settings.masked_key('huggingface_api_key')}`")
    st.sidebar.markdown(f"**Google Gemini:** `{settings.masked_key('gemini_api_key')}`")
    
    db_exists = settings.absolute_db_path.exists()
    st.sidebar.markdown(f"**SQLite Database:** `{'Active' if db_exists else 'Not Initialized'}`")
    st.sidebar.markdown(f"**Environment:** `{settings.app_env.upper()}`")
    
    st.sidebar.markdown("---")
    st.sidebar.markdown(
        """
        **Target Geography:** Pune City & PCMC  
        **Grid Regulator:** MSEDCL  
        **Execution Mode:** Local-First  
        """
    )


def main():
    """Main application layout and tab navigation."""
    render_sidebar()

    st.title("AI-Based International Solar Technology Partner Matching Agent")
    st.subheader("Rooftop Solar Projects in Pune City | UN SDG 7.A International Clean Energy Cooperation")

    st.info(
        "🌿 **UN SDG 7, Target 7.A Alignment:** Enhancing international cooperation to facilitate access to clean energy "
        "research, technology, and verified international solar technology partners for Pune's residential, housing society, "
        "commercial, and institutional rooftops."
    )

    tab_overview, tab_intake, tab_matches, tab_catalog, tab_reports = st.tabs([
        "📋 Overview & Guidelines",
        "🏗️ Project Intake",
        "🎯 Matching Results",
        "📚 Provider Knowledge Base",
        "📑 Collaboration Report"
    ])

    with tab_overview:
        st.markdown("### Pune Rooftop Solar Context")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(label="Primary Geography", value="Pune & PCMC")
        with col2:
            st.metric(label="Grid Interconnection", value="MSEDCL Net-Metered")
        with col3:
            st.metric(label="Core Scope", value="Rooftop PV + Storage")

        st.markdown(
            """
            #### How It Works:
            1. **Intake & Normalization:** Define building type, target capacity (kW), roof conditions, and Pune locality.
            2. **Stage 1 Hard Filtering:** Disqualifies providers outside project capacity or without verifiable India presence.
            3. **Stage 2 Compatibility Scoring:** Evaluates multi-dimensional fit across technology, local service footprint, BIS/IEC certifications, and budget alignment.
            4. **Evidence-Grounded Reporting:** Synthesizes actionable partner collaboration recommendations backed by authenticated datasheets and transparent due-diligence callouts.
            """
        )

    with tab_intake:
        st.write("Project Intake Form will be activated in Phase 4.")

    with tab_matches:
        st.write("Matching Engine results and scoring breakdown will be displayed here in Phase 4.")

    with tab_catalog:
        st.write("Curated international provider knowledge base will be displayed here in Phase 2 & 4.")

    with tab_reports:
        st.write("Collaboration recommendation reports will be generated here in Phase 6.")


if __name__ == "__main__":
    main()
