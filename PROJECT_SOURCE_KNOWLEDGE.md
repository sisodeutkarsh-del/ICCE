# PROJECT SOURCE KNOWLEDGE

**Project Title:** AI-Based International Solar Technology Partner Matching Agent for Rooftop Solar Projects in Pune City  
**Repository Role:** Authoritative Canonical Knowledge Specification  
**Document Version:** 1.0.0  
**Status:** Canonical Baseline (Active)  
**Last Updated:** 2026-10-24  

---

## 1. Project Identity & Overview

The **AI-Based International Solar Technology Partner Matching Agent for Rooftop Solar Projects in Pune City** is a local-first, modular software application designed to connect rooftop solar initiatives across Pune City, Maharashtra, India, with verified, capable international technology providers, equipment manufacturers, and technical partners.

### 1.1 SDG Alignment
- **United Nations Sustainable Development Goal 7:** Ensure access to affordable, reliable, sustainable, and modern energy for all.
- **Target 7.A:** By 2030, enhance international cooperation to facilitate access to clean energy research and technology, including renewable energy, energy efficiency, and advanced and cleaner fossil-fuel technology, and promote investment in energy infrastructure and clean energy technology.

### 1.2 Core Problem Statement
Pune City experiences robust solar irradiation and rapid urban expansion across residential, cooperative housing society, educational, and commercial sectors. However, project developers, housing society committees, institutional managers, and commercial building operators face significant challenges when identifying appropriate international solar technology providers:
1. **Fragmented Technical Data:** Technical specifications (PV module efficiency, inverter topologies, degradation rates, temperature coefficients, battery chemistry) are distributed across fragmented datasheets, corporate portals, and marketing literature.
2. **Local Support Ambiguity:** International manufacturers often lack clearly verified local channel partners, warranty fulfillment infrastructure, or authorized technical support networks in Maharashtra or India.
3. **Mismatched Sizing & Requirements:** Rooftop solar projects in Pune have distinct microclimatic conditions (monsoon cloud cover, high summer ambient temperatures, dust accumulation), spatial limitations (shading from water tanks, parapets, lift rooms), and grid integration constraints (MSEDCL net-metering guidelines).
4. **Information Asymmetry & Marketing Bias:** Non-technical consumers and society committees frequently receive commercially biased advice without verifiable provenance or transparent trade-off analyses.

### 1.3 Solution Hypothesis
A locally runnable, evidence-grounded AI agent that combines:
- A curated, source-attributed, schema-validated knowledge base of international solar technology providers;
- Deterministic, explainable multi-criteria compatibility scoring with explicit hard eligibility filters;
- Traceable citations (official URLs, verified datasheets, timestamped records);
- A provider-neutral Large Language Model (LLM) interface with automatic fallback for requirement analysis and natural-language synthesis;
- A local-first Streamlit graphical interface backed by SQLite and local JSON/CSV registries.

---

## 2. Project Scope & Operational Boundaries

### 2.1 Geographic & Climatic Scope
- **Target Location:** Pune City Municipal Corporation (PMC) and Pimpri-Chinchwad Municipal Corporation (PCMC) boundaries, Maharashtra, India.
- **Local Context:** Grid interconnected under Maharashtra State Electricity Distribution Company Limited (MSEDCL) net-metering regulations. Tropical wet-and-dry climate characterized by high pre-monsoon temperatures (March–May), heavy south-west monsoon precipitation (June–September), and mild dry winters.

### 2.2 Technology Scope
- **Primary Technology:** Rooftop Solar Photovoltaic (PV) systems:
  - Monocrystalline PERC, TOPCon, and Heterojunction (HJT) module technologies;
  - String inverters, microinverters, and hybrid inverter systems.
- **Secondary / Optional Extensions:**
  - Battery Energy Storage Systems (BESS) (Lithium Iron Phosphate - LiFePO4, high-cycle storage);
  - Smart Monitoring, IoT Energy Management Systems, and zero-export controllers.

### 2.3 User Groups & Archetypes
1. **Residential Individual Homeowners (Bunglows/Villas):** Typical capacity 2 kW to 10 kW. Priorities: aesthetics, safety, microinverters or rapid shutdown, simplified MSEDCL net metering, low maintenance.
2. **Cooperative Housing Societies (CHS / Apartment Complexes):** Typical capacity 10 kW to 100+ kW (common area lighting, water pumping, EV charging). Priorities: verifiable long-term warranty, certified Indian service centers, phased capital expenditure, net-metering compliance.
3. **Educational Institutions & Campuses:** Typical capacity 50 kW to 500 kW. Priorities: educational monitoring dashboards, high durability, institutional tender compliance, tier-1 international reliability.
4. **Commercial & Industrial Buildings:** Typical capacity 25 kW to 1000+ kW. Priorities: high-efficiency TOPCon/HJT modules for constrained roof area, rapid ROI, low Levelized Cost of Electricity (LCOE), comprehensive SCADA/remote monitoring.

### 2.4 Project Constraints & Non-Goals
- **Local Development Only:** Designed exclusively for local execution on developer/user workstations. No cloud hosting, no remote database instances, and no public SaaS deployment required.
- **No Physical Hardware or Installation:** The system does not interface with physical inverters or perform physical site surveying.
- **No Hardcoded Magic Recommendations:** Every recommendation must be derived deterministically from the knowledge base and transparent scoring algorithms.
- **Zero Hallucination Policy:** Unknown technical specs or missing local contact details must be preserved as `None` / `UNKNOWN`. Missing fields must penalize or flag uncertainty, never be replaced by optimistic inventions.
- **Offline Core Operation:** Core search, filtering, deterministic scoring, and recommendation generation must function with 100% reliability with zero internet connection and without any external API keys.

---

## 3. System Architecture & Component Design

The application follows a **Local-First Layered Hexagonal / Clean Architecture** pattern with clear boundaries between the user interface, application services, domain business rules, and external adapters.

```
+-----------------------------------------------------------------------------------+
|                            STREAMLIT USER INTERFACE                               |
|   (app.py - Project Intake, Filter Sliders, Match Results, Provider Details,      |
|    Evidence Inspector, Report Generator, Local Provider Health / Status View)     |
+-----------------------------------------------------------------------------------+
                                      |
                                      v
+-----------------------------------------------------------------------------------+
|                                SERVICES LAYER                                     |
|  - RequirementAnalyzerService (Normalizes project profile & technical constraints)|
|  - ProviderSearchService (Applies hard eligibility filters & candidate queries)  |
|  - CompatibilityScoringService (Deterministic weighted scoring & metric breakdown)|
|  - ExplanationService (Synthesizes factual evidence & explains score drivers)     |
|  - RecommendationReportService (Compiles Markdown / JSON / PDF-ready summaries)   |
+-----------------------------------------------------------------------------------+
                                      |
                                      v
+-----------------------------------------------------------------------------------+
|                                 DOMAIN LAYER                                      |
|  - ProjectProfile (Pydantic validated intake schema)                              |
|  - ProviderRecord (Pydantic validated international solar technology provider)    |
|  - CompatibilityScore (Breakdown across 6 core criteria, total score 0-100)       |
|  - MatchResult (Ranked candidate, justification, missing data warnings)           |
|  - EvidenceCitation (Verified source URL, claim, last_verified timestamp)         |
+-----------------------------------------------------------------------------------+
                     |                                           |
                     v                                           v
+------------------------------------------+ +--------------------------------------+
|             DATA ACCESS LAYER            | |          LLM GATEWAY LAYER           |
| - SQLiteProviderRepository               | | - LLMGateway (Unified Interface)     |
| - LocalFileImporter (JSON/CSV with source| | - Adapters: OpenRouter, Gemini,      |
|   attribution & deduplication)           | |   HuggingFace, Local Mock / Null     |
| - LocalProjectHistoryRepository          | | - FallbackOrchestrator (Retries,     |
| - Curated Data vs Sample Fixture Guard   | |   Exponential Backoff, Circuit Breaker)
+------------------------------------------+ +--------------------------------------+
                     |                                           |
                     v                                           v
         [Local SQLite DB / Files]                     [External LLM APIs]
          (solar_agent.db, data/)                       (Optional, Key-Gated)
```

### 3.1 Architectural Invariants
1. **Dependency Rule:** Source code dependencies point inward. Domain models have zero dependencies on Streamlit, SQLite, or external API client libraries.
2. **Provider-Neutral LLM Isolation:** Business logic never invokes `openai`, `google.generativeai`, or raw HTTP requests directly. All model calls route through `LLMGateway` implementing `BaseLLMAdapter`.
3. **Auditability & Provenance:** Every `ProviderRecord` must contain an `evidence` list referencing specific source URLs, publisher types, and verification dates.

---

## 4. Domain Data Model & Schema Specification

All domain entities are strictly typed and validated using **Pydantic v2** models.

### 4.1 Project Profile Schema (`ProjectProfile`)
| Field | Type | Required | Description & Validation |
| :--- | :--- | :--- | :--- |
| `project_id` | `str` | Yes | UUID4 string identifier |
| `project_name` | `str` | Yes | 3 to 100 characters |
| `pune_locality` | `str` | Yes | Pune neighborhood (e.g., Kothrud, Baner, Hadapsar, Hinjawadi, PCMC) |
| `building_type` | `BuildingType` | Yes | Enum: `RESIDENTIAL_INDIVIDUAL`, `HOUSING_SOCIETY`, `COMMERCIAL`, `EDUCATIONAL`, `INDUSTRIAL` |
| `target_capacity_kw` | `float` | Yes | Range: 1.0 kW to 2000.0 kW |
| `budget_inr` | `Optional[float]`| No | If provided, must be > 0.0 |
| `roof_type` | `RoofType` | Yes | Enum: `RCC_FLAT`, `METAL_SHED`, `TILED_SLOPE`, `OPEN_TERRACE_MIXED` |
| `technology_preference`| `List[TechType]`| Yes | Subset of: `MONO_PERC`, `TOPCON`, `HJT`, `STRING_INVERTER`, `MICROINVERTER`, `HYBRID_INVERTER`, `BESS_LFP` |
| `grid_coupling` | `GridCoupling` | Yes | Enum: `ON_GRID_NET_METERED`, `OFF_GRID`, `HYBRID_STORAGE` |
| `service_requirement` | `ServiceLevel`| Yes | Enum: `LOCAL_PUNE_OFFICE`, `MAHARASHTRA_SERVICE_NETWORK`, `PAN_INDIA_AUTHORIZED_PARTNER`, `REMOTE_INTERNATIONAL_SUPPORT` |
| `priority_weights` | `Optional[Dict]`| No | Optional custom user weights for scoring criteria |

### 4.2 Evidence Item Schema (`EvidenceCitation`)
| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `citation_id` | `str` | Yes | Unique citation identifier |
| `claim` | `str` | Yes | Verifiable technical or support claim |
| `source_url` | `HttpUrl` | Yes | Verified web URL or official document reference |
| `source_type` | `SourceType` | Yes | Enum: `OFFICIAL_PORTAL`, `PRODUCT_DATASHEET`, `CERTIFICATION_BODY`, `GOVT_TENDER_RECORD`, `INDUSTRY_DIRECTORY` |
| `last_verified` | `date` | Yes | ISO date when information was verified |
| `verification_note` | `str` | Yes | Verification methodology or note |

### 4.3 Provider Record Schema (`ProviderRecord`)
| Field | Type | Required | Description & Validation |
| :--- | :--- | :--- | :--- |
| `provider_id` | `str` | Yes | Unique slug/ID (e.g., `prv_sma_solar_de`) |
| `name` | `str` | Yes | Legal/Commercial brand name |
| `headquarters_country` | `str` | Yes | ISO country name or 2-letter code |
| `primary_technologies` | `List[TechType]` | Yes | Verified technology categories |
| `min_capacity_kw` | `float` | Yes | Minimum viable project capacity supported |
| `max_capacity_kw` | `float` | Yes | Maximum project capacity supported |
| `supported_building_types`| `List[BuildingType]`| Yes | Target building sectors |
| `india_presence_type` | `IndiaPresence` | Yes | Enum: `DIRECT_SUBSIDIARY`, `AUTHORIZED_DISTRIBUTOR`, `CERTIFIED_EPC_NETWORK`, `IMPORT_ONLY_NO_LOCAL_OFFICE`, `NONE` |
| `pune_service_availability`| `bool` | Yes | True if verified service/channel partner covers Pune/PCMC |
| `in_country_warehouse` | `bool` | Yes | True if spare parts warehouse exists in India |
| `certifications` | `List[str]` | Yes | Recognized standards (e.g., IEC 61215, IEC 62109, BIS CRS, UL 1741) |
| `warranty_terms` | `Dict[str, Any]`| Yes | Product and performance warranty details (e.g., 25-yr performance, 12-yr product) |
| `estimated_cost_tier` | `CostTier` | Yes | Enum: `ECONOMY`, `MID_RANGE`, `PREMIUM_TIER1`, `HIGH_END_SPECIALTY` |
| `evidence_records` | `List[EvidenceCitation]`| Yes | Must contain at least 1 verified citation |
| `is_sample_data` | `bool` | Yes | Explicit flag: `True` if synthetic fixture, `False` if fully verified |
| `last_audit_date` | `date` | Yes | Date record was audited |

---

## 5. Provider Sourcing & Data Quality Strategy

### 5.1 Verified vs Sample Data Separation
- **Verified Records (`data/verified_providers.json`):** Contains exclusively authenticated provider profiles backed by live official datasheets, corporate registrations in India, and BIS/IEC certification numbers.
- **Sample Fixtures (`data/sample_fixtures.json`):** Clearly labeled mock records (`"is_sample_data": true`) used for testing edge cases, capacity boundary tests, and malformed data handling.
- **Storage Segregation:** SQLite records maintain a boolean column `is_sample_data`. UI filters allow users to inspect verified records only, sample records only, or all records with prominent visual badges.

### 5.2 Mandatory Evidence Standard
No provider record is accepted into the verified registry without:
1. An official manufacturer website or datasheet URL.
2. Verifiable IEC/BIS compliance indicator where required by Indian regulations (MNRE/MSEDCL grid code requires BIS certification for modules and inverters).
3. Explicit presence declaration for Indian operations (Direct subsidiary, distributor, or remote).

### 5.3 Handling Unknowns & Missing Facts
- When a datasheet does not state maximum ambient operating temperature, warranty claim contact in India, or local pricing, the field is stored as `null`.
- The matching engine treats `null` as **uncertain / missing**, never as a positive match.
- Missing fields are aggregated in the `MatchResult.missing_fields` list and presented explicitly to the user as due-diligence items.

---

## 6. Deterministic Matching Engine & Scoring Methodology

The matching engine operates in two sequential stages: **Stage 1 (Hard Eligibility Filtering)** and **Stage 2 (Weighted Compatibility Scoring)**.

### 6.1 Stage 1: Hard Eligibility Filters (Gates)
A candidate provider is disqualified (`status = DISQUALIFIED`) if any of the following gates fail:
1. **Technology Overlap Gate:** Provider must manufacture or supply at least one technology specified in `ProjectProfile.technology_preference`.
2. **Capacity Feasibility Gate:** The project's `target_capacity_kw` must satisfy:
   $$\text{min\_capacity\_kw} \le \text{target\_capacity\_kw} \le \text{max\_capacity\_kw}$$
3. **Sector Applicability Gate:** The project's `building_type` must be present in `supported_building_types`.
4. **Minimum India Presence Gate:** If the user requires `LOCAL_PUNE_OFFICE` or `MAHARASHTRA_SERVICE_NETWORK`, providers with `NONE` or `IMPORT_ONLY_NO_LOCAL_OFFICE` without local channel partners are filtered out.

Only candidates passing all Stage 1 gates proceed to Stage 2.

### 6.2 Stage 2: Multi-Criteria Compatibility Scoring Formula
Scoring produces a normalized score $S \in [0, 100]$ computed as a weighted sum of six orthogonal sub-scores:

$$S = \sum_{i=1}^{6} (w_i \cdot s_i) - P_{\text{missing}}$$

Where $\sum w_i = 1.0$, $s_i \in [0, 100]$, and $P_{\text{missing}}$ is an explicit penalty for unverified critical data.

#### Configurable Default Weights
| Metric | Weight ($w_i$) | Dimension Evaluated |
| :--- | :---: | :--- |
| **Technology Compatibility ($s_{\text{tech}}$)** | $0.25$ | Degree of match with requested module/inverter/storage types |
| **Capacity & Specification Fit ($s_{\text{cap}}$)** | $0.20$ | Proximity to optimal operating scale (sweet spot of provider product line) |
| **India & Pune Service Footprint ($s_{\text{svc}}$)** | $0.20$ | Local office in Pune/Mumbai, spare parts warehouse, direct engineers |
| **Certifications & Compliance ($s_{\text{cert}}$)** | $0.15$ | BIS CRS registration, IEC 61215/61730/62109, MSEDCL compliance |
| **Evidence & Documentation ($s_{\text{doc}}$)** | $0.10$ | Depth of public datasheets, verified source links, warranty clarity |
| **Budget & Cost Feasibility ($s_{\text{cost}}$)** | $0.10$ | Compatibility between user's budget tier and provider's cost tier |

#### Sub-Score Calculation Rules
1. **Technology Fit ($s_{\text{tech}}$):**
   $$s_{\text{tech}} = \frac{|\text{Project Tech} \cap \text{Provider Tech}|}{|\text{Project Tech}|} \times 100$$
2. **Capacity Fit ($s_{\text{cap}}$):**
   Let $C = \text{target\_capacity\_kw}$. If $C$ is in the optimal mid-range $[1.5 \times \min, 0.8 \times \max]$, $s_{\text{cap}} = 100$. Near boundary limits, score decays linearly to 60.
3. **Service Footprint ($s_{\text{svc}}$):**
   - Direct Pune presence + local warehouse: $100$
   - Maharashtra regional presence (Mumbai/Pune channel): $85$
   - Pan-India distributor network: $70$
   - Import only with 3rd-party tie-up: $40$
   - Unknown/Unspecified: $15$
4. **Certifications ($s_{\text{cert}}$):**
   - BIS Certified + Full IEC suite: $100$
   - Full IEC suite (pending/verified BIS): $80$
   - Standard international certifications only: $60$
   - Incomplete certification evidence: $30$
5. **Evidence Completeness ($s_{\text{doc}}$):**
   Calculated based on verified citation count, presence of official datasheets, and recent audit date within 365 days.
6. **Budget Feasibility ($s_{\text{cost}}$):**
   If budget is provided, aligns user INR/kW expectation with manufacturer cost tier. If budget is unstated, neutral score ($70$) is awarded and flagged as unconstrained.
7. **Missing Data Penalty ($P_{\text{missing}}$):**
   $$P_{\text{missing}} = 5 \times (\text{Number of critical unknown fields})$$
   (Capped at 25 points maximum deduction to prevent negative scores).

### 6.3 Explainability Metadata
Every match result outputs:
- **Total Compatibility Score:** 0 to 100 with qualitative tier (Exceptional: 85+, Strong: 70–84, Moderate: 50–69, Low: <50).
- **Sub-score Radar / Breakdown:** Transparent numerical value for each $s_i$.
- **Positive Drivers:** Top 3 factors elevating the score.
- **Risk & Limitation Flags:** Penalties incurred, missing documentation, or service network gaps.
- **Traceable Citations:** Direct hyperlinks to the underlying manufacturer datasheets.

---

## 7. Model-Provider Abstraction & Fallback Orchestration

The application includes an optional LLM gateway for extracting project requirements from unstructured text and synthesizing natural-language executive summaries of recommendations.

### 7.1 Provider-Neutral Interface
The abstraction is defined by an abstract base class `BaseLLMAdapter`:
```python
class BaseLLMAdapter(ABC):
    @abstractmethod
    def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        pass
        
    @abstractmethod
    def extract_structured(self, prompt: str, schema: Type[BaseModel]) -> LLMStructuredResponse:
        pass

    @abstractmethod
    def health_check(self) -> ProviderHealthStatus:
        pass
```

### 7.2 Supported Model Providers
1. **Google Gemini:** Direct integration via `google-genai` / REST API.
2. **OpenRouter:** Multi-model routing (Llama-3, Mistral, Claude, GPT) via OpenAI-compatible endpoints.
3. **Hugging Face Inference:** Serverless inference endpoints for open-weights models.
4. **Offline / Null Mock Adapter:** Deterministic fallback when no API keys are present or all networks fail.

### 7.3 Resilience & Fallback Orchestration
```
User / Service Request
       |
       v
[LLMGateway]
       |
       +---> Try Provider 1 (e.g. Gemini) --- Success ---> Return Validated Response
       |           |
       |       Timeout / 429 / 5xx (Retryable)
       |           v
       |     [Exponential Backoff + Jitter] (Max 2 retries)
       |           |
       |       Failed / Exhausted
       |           v
       +---> Fallback to Provider 2 (e.g. OpenRouter) --- Success ---> Return Response
       |           |
       |       Failed / 401 / Quota
       |           v
       +---> Fallback to Provider 3 (e.g. Hugging Face)
       |           |
       |       All External Providers Failed
       |           v
       +---> [Deterministic Fallback Engine]
             - Inform user LLM synthesis is offline
             - Return rule-based requirement extraction and template-driven reports
             - Zero application crash
```

### 7.4 Security & Key Management
- **No Embedded Secrets:** Keys are read exclusively from environment variables (`OPENROUTER_API_KEY`, `GEMINI_API_KEY`, `HUGGINGFACE_API_KEY`) or a local, uncommitted `.env` file.
- **Sanitized UI & Logging:** Secret values are never printed, displayed in Streamlit, written to logs, or embedded in exported reports. Masks (e.g., `sk-...4a2b`) are used in health-check views.
- **Permanent vs Retryable Errors:**
  - `401 Unauthorized` / `403 Forbidden`: Mark provider as unhealthy immediately; do not retry; proceed to next provider.
  - `429 Rate Limit`: Inspect `Retry-After` header; back off if within budget (< 5s), otherwise switch to fallback.
  - `500 / 503 Server Error`: Exponential backoff with jitter (initial 1.0s, multiplier 2.0, max 2 attempts).

---

## 8. User Interface Specification (Streamlit)

The UI is built with Streamlit using standard, robust components and a structured layout:
1. **Sidebar Navigation & Configuration:**
   - Active Mode indicator (Offline / Live LLM);
   - Provider Registry Selector (All, Verified Only, Include Sample Fixtures);
   - Model Provider Health Status dashboard (latency, status, masked key indicators);
   - Weight Tuning Accordion (advanced users can adjust scoring criteria weights).
2. **Tab 1: Project Intake & Requirements Profiling:**
   - Structured input form (Building type, locality dropdown for Pune, capacity slider/input, budget, roof type, technology checklist);
   - Natural language quick-intake box (optional LLM-assisted requirement extraction);
   - Real-time Pydantic validation error banners.
3. **Tab 2: Partner Matching & Ranked Recommendations:**
   - Summary of qualified vs disqualified providers;
   - Ranked provider recommendation cards with overall compatibility score badges;
   - Detailed score breakdown (radar chart / progress metrics for the 6 sub-scores);
   - Evidence inspector drawer showing verified datasheets and last-audit timestamps;
   - Missing information and risk warning callouts.
4. **Tab 3: Provider Knowledge Base Explorer:**
   - Filterable data table of international providers (search by country, technology, capacity);
   - Source citation viewer with clickable outbound URLs;
   - Import tool for adding new validated provider records via CSV or JSON.
5. **Tab 4: Collaboration Report & Export:**
   - Formatted UN SDG 7.A aligned Collaboration Recommendation Report;
   - Download buttons for Markdown (`.md`) and JSON (`.json`) report artifacts.

---

## 9. Local-First Engineering & Verification Standards

### 9.1 Storage Architecture
- Local SQLite database (`database/solar_agent.db`) managed via clean Python SQL repositories.
- Deterministic initialization scripts (`database/init_db.py`).
- JSON/CSV data files in `data/` serving as source-controlled seed catalogs.

### 9.2 Automated Testing Strategy
- **Unit Tests (`tests/unit/`):**
  - Validation of `ProjectProfile` and `ProviderRecord` Pydantic schemas;
  - Boundary conditions for Stage 1 hard eligibility filters;
  - Exact mathematical verification of Stage 2 weighted scoring formulas;
  - Missing field penalty calculations.
- **Integration Tests (`tests/integration/`):**
  - SQLite repository CRUD operations and duplicate record prevention;
  - File importer parsing and schema enforcement;
  - LLM gateway fallback order and graceful degradation to deterministic mode;
  - End-to-end matching pipeline (Input Profile -> Ranked Output -> Report Generation).
- **Test Fixtures (`tests/fixtures/`):**
  - Fully deterministic mock project profiles and provider datasets for repeatable, offline test runs.

---

## 10. Risk Management & Ethical Safeguards

1. **Non-Commercial Impartiality:** The application does not promote any commercial brand over another. Rankings are strictly derived from documented specs and verified presence.
2. **Disclaimers & Limitations:** Every report explicitly states:
   - "This report is an AI-assisted preliminary technical compatibility screening and does not constitute a formal structural engineering audit, financial investment advice, or commercial contract."
   - "Final structural load verification, electrical sanctioning from MSEDCL, and MNRE subsidy eligibility must be verified by licensed EPC contractors in Pune."
3. **No Hallucinated URLs or Specifications:** Any unverified parameter must remain tagged as unknown.

---

## 11. Canonical Acceptance Criteria

1. Application starts locally on Windows PowerShell using a single documented command (`streamlit run app.py`).
2. User can submit a Pune rooftop solar project profile through validated input controls.
3. Real provider records can be imported, validated, and queried in local storage.
4. Matching and ranking are deterministic, mathematically explainable, and verified by automated unit tests.
5. Recommendations include traceable evidence links, verified timestamps, and disclosed unknowns.
6. The application handles missing data, edge capacities, and zero-match states gracefully with actionable guidance.
7. Optional LLM features use configured provider adapters with automatic fallback and respectful rate-limiting.
8. Core matching and recommendation workflows function completely offline with zero API keys.
9. Secrets and API keys are protected and never logged, printed, or exposed in UI views.
10. Automated test suite runs reliably offline with high coverage across core modules.
11. Both canonical documents (`PROJECT_SOURCE_KNOWLEDGE.md` and `PROJECT_ROADMAP.md`) accurately reflect implementation reality at all times.
12. Zero deployment to external cloud servers; 100% workstation-contained execution.

---

## 12. Verification Records & Final System Metrics

- **Verified Test Count:** 51 / 51 Automated Tests Passing (100% Pass Rate).
  - 43 Unit Tests across domain models, SQLite repository, importer, matching engine, LLM gateway, report generator, and UI helpers.
  - 8 End-to-End Integration Tests across realistic Pune scenarios, capacity limits, zero-match resilience, offline operation, and security audits.
- **Seeded Knowledge Base:** 9 total providers (6 authentic verified international providers active in India, 3 synthetic fixtures segregated by `is_sample_data`).
- **Demonstration Scenarios Executed:**
  - Scenario 1 (Kothrud Housing Society, 35 kW): Top match SMA Solar (82.7/100, Strong Match), 5 eligible.
  - Scenario 2 (Baner Bungalow, 6 kW): Top match Enphase Energy (81.8/100, Strong Match), 3 eligible.
  - Scenario 3 (Hinjawadi IT Park, 150 kW): Top match SMA Solar (82.7/100, Strong Match), 4 eligible.
- **Offline & Fallback Guarantee:** Validated zero external cloud dependency; `FallbackOrchestrator` smoothly degrades to `MockDeterministicAdapter` under 404/429/timeout conditions.
- **Security Audit:** Zero secrets or API keys leaked in repositories, log streams, or exported report artifacts.
- **Final Status:** Fully Verified and Production-Ready on Local Workstation.

