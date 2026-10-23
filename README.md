# ☀️ SolarMatch Pune: AI International Solar Technology Partner Matching Agent

[![UN SDG 7.A](https://img.shields.io/badge/UN%20SDG-7.A%20Clean%20Energy%20Cooperation-E5243B?style=for-the-badge&logo=united-nations&logoColor=white)](https://sdgs.un.org/goals/goal7)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.42+-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![SQLite](https://img.shields.io/badge/Database-SQLite%203-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Tests Passing](https://img.shields.io/badge/Tests-51%2F51%20Passed%20(100%25)-10B981?style=for-the-badge&logo=pytest&logoColor=white)](tests/)
[![Security](https://img.shields.io/badge/Security-Zero%20Secret%20Leakage-10B981?style=for-the-badge&logo=shield&logoColor=white)](config/settings.py)

> **Locally runnable, evidence-grounded AI agent matching rooftop solar projects in Pune City with verified international clean-energy technology partners under UN Sustainable Development Goal 7, Target 7.A.**

---

## 📌 1. Project Overview & UN SDG Alignment

### The Problem in Pune City
Urban rooftop solar adoption in Pune, Maharashtra faces unique friction:
- **Residential Bungalows & Row Houses (e.g., Baner, Aundh):** Require shade-resilient architectures (microinverters, DC optimizers) and local service networks.
- **Cooperative Housing Societies / CHS (e.g., Kothrud, Karve Nagar):** Require common-meter net-metering, high reliability string inverters, and General Body Resolution (GBM) compliance under MSEDCL rules.
- **Commercial & IT Campuses (e.g., Hinjawadi, Magarpatta):** Require megawatt-class high-efficiency TOPCon modules, metal-shed mounting compatibility, and Chief Electrical Inspector (CEI) approval for systems $>100\text{ kW}$.

Identifying international clean-technology providers whose products, certifications (BIS CRS / IEC), and Pune service networks align with these requirements is manual and fragmented.

### The Solution
**SolarMatch Pune** is a 100% locally runnable, deterministic AI agent that:
1. Sockets project requirements against Pune climatic conditions ($1{,}500\text{ kWh/kWp/year}$) and MSEDCL net-metering regulations.
2. Filters international providers through 4 Stage-1 hard eligibility gates.
3. Ranks candidates using a 6-dimension transparent multi-criteria formula.
4. Generates audit-ready recommendation reports (Markdown & JSON) with clickable datasheets and BIS/IEC citations.
5. Operates 100% offline via a built-in deterministic fallback engine while supporting OpenRouter, Gemini, and Hugging Face when configured.

---

## 🏗️ 2. Architectural Blueprint

```
                          ┌────────────────────────┐
                          │   Project Intake Form  │
                          │   (Streamlit / Python) │
                          └───────────┬────────────┘
                                      │
                                      ▼
                        ┌───────────────────────────┐
                        │ RequirementAnalyzerService│
                        │ • Pune 1500 kWh/kW yield  │
                        │ • 100 sq.ft/kW area sizing│
                        │ • MSEDCL net-meter rules  │
                        └─────────────┬─────────────┘
                                      │
                                      ▼
     ┌─────────────────────────────────────────────────────────────────┐
     │                    MatchingService Engine                       │
     │                                                                 │
     │  Stage 1: Hard Eligibility Filtering (ProviderSearchService)   │
     │  ├── Technology overlap ≥ 1 requested tech                      │
     │  ├── Operating scale [min_kw, max_kw]                           │
     │  ├── Building sector fit (Residential, Commercial, CHS)        │
     │  └── In-country presence gate (Subsidiary, Pune office, SLA)    │
     │                                                                 │
     │  Stage 2: Multi-Criteria Compatibility Scoring (ScorerService)  │
     │  ├── S_tech (25%)   + S_capacity (20%) + S_service (20%)       │
     │  └── S_cert (15%)   + S_doc (10%)      + S_cost (10%)          │
     │      └── Minus Missing Field Penalty (P_missing)                │
     └─────────────────┬───────────────────────────────┬───────────────┘
                       │                               │
                       ▼                               ▼
       ┌───────────────────────────────┐ ┌─────────────────────────────┐
       │   Provider Knowledge Base     │ │    LLM Gateway (Fallback)   │
       │   • SQLite3 (solar_agent.db)  │ │ • Primary: OpenRouter       │
       │   • 6 Authenticated Providers │ │ • Secondary: Gemini         │
       │   • Strict Evidence Citations │ │ • Tertiary: Hugging Face    │
       │   • Data Segregation Flag     │ │ • Offline: MockDeterministic│
       └───────────────────────────────┘ └──────────────┬──────────────┘
                                                       │
                                                       ▼
                                      ┌────────────────────────────────┐
                                      │ RecommendationReportService    │
                                      │ • Markdown (.md) Export        │
                                      │ • JSON Schema (.json) Export   │
                                      │ • Verified Citation Inspector  │
                                      └────────────────────────────────┘
```

---

## ⚙️ 3. Sizing & Mathematical Scoring Formulas

### 3.1 Pune Solar Sizing Engineering Constants
$$\text{Annual Generation (kWh)} = \text{Target Capacity (kW)} \times 1{,}500\text{ kWh/kWp/year}$$
$$\text{Estimated Roof Area (sq.ft)} = \text{Target Capacity (kW)} \times 100\text{ sq.ft/kW}$$
$$\text{Annual }\text{CO}_2\text{ Offset (tons)} = \frac{\text{Annual Generation (kWh)} \times 0.82\text{ kg/kWh}}{1{,}000}$$

### 3.2 Stage-2 Multi-Criteria Compatibility Score
$$S_{\text{total}} = \max\left(0, \sum_{i=1}^{n} (w_i \cdot s_i) - P_{\text{missing}}\right)$$

Where default weights are:
- $w_{\text{tech}} = 0.25$ (Technology Specification Fit)
- $w_{\text{capacity}} = 0.20$ (Operating Scale Sweet-Spot)
- $w_{\text{service}} = 0.20$ (India Subsidiary, Pune Office, Spares Warehouse)
- $w_{\text{cert}} = 0.15$ (Dual BIS CRS + IEC Compliance)
- $w_{\text{doc}} = 0.10$ (Product Datasheet & Verification Freshness)
- $w_{\text{cost}} = 0.10$ (Budget Feasibility Alignment)
- $P_{\text{missing}} = 5.0\text{ pts}$ per critical missing data attribute

Qualitative Tiers:
- **$\ge 85.0$:** Exceptional Match (Tier 1)
- **$70.0 - 84.9$:** Strong Match (Tier 2)
- **$50.0 - 69.9$:** Moderate Match (Tier 3)
- **$< 50.0$:** Low / Marginal Match (Tier 4)

---

## 🚀 4. Quickstart Guide

### 4.1 System Prerequisites
- **Operating System:** Windows 10/11, macOS, or Linux.
- **Python Version:** Python 3.10, 3.11, 3.12, or 3.13.
- **Internet Access:** Optional (system functions 100% offline out-of-the-box).

### 4.2 Clone & Environment Setup
Open Windows PowerShell (or terminal):
```powershell
# 1. Clone repository
git clone https://github.com/sisodeutkarsh-del/ICCE.git
cd ICCE

# 2. (Optional) Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt
```

### 4.3 Configure Environment (.env)
Copy `.env.example` to `.env`:
```powershell
Copy-Item .env.example .env
```
*(Optional: add your API keys to `.env` if external LLM generation is desired. If left blank, the application automatically uses the built-in deterministic offline engine with zero errors.)*

### 4.4 Seed Database
Populate SQLite database (`database/solar_agent.db`) with verified authentic international technology partners and sample fixtures:
```powershell
python -m database.seed_db
```

### 4.5 Launch Streamlit Application
```powershell
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 🧪 5. Automated Test Suite (51 / 51 Passed)

Run the full automated test suite offline:
```powershell
python -m pytest -v
```

### Test Suite Structure
| Test Suite | File | Tests | Coverage Scope |
| :--- | :--- | :---: | :--- |
| **Integration Suite** | `tests/integration/test_end_to_end_pipeline.py` | 8 | Baner, Kothrud, Hinjawadi E2E, 1 kW to 1500 kW bounds, zero-match, secret audit |
| **Domain Models** | `tests/unit/test_domain_models.py` | 6 | Pydantic v2 schemas, capacity ranges, URL validations, enum integrity |
| **Foundation** | `tests/unit/test_foundation.py` | 5 | Key masking, logger token redaction, DB schema creation, sample fixtures |
| **Data Importer** | `tests/unit/test_importer.py` | 4 | JSON data import, deduplication, schema validation, error handling |
| **LLM Gateway** | `tests/unit/test_llm_gateway.py` | 7 | Fail-fast 401/403, retry 429/5xx, graceful fallback, offline deterministic mock |
| **Matching Engine** | `tests/unit/test_matching_engine.py` | 10 | Hard gates, 6-factor scoring, penalty deductions, explanation generator |
| **Repository** | `tests/unit/test_provider_repository.py` | 5 | SQLite upsert, ID query, verified flag filtering, cascade evidence deletion |
| **Reports** | `tests/unit/test_reports.py` | 3 | Markdown report layout, JSON schema structure, end-to-end agent workflow |
| **UI Helpers** | `tests/unit/test_ui_helpers.py` | 3 | Tier badge HTML, color mapping, Pune scenario presets presence |
| **Total** | — | **51** | **100% Pass Rate across all suites** |

---

## 📊 6. Pune Demonstration Scenarios & Evaluation Results

Execute all three pre-configured demonstration scenarios in one command:
```powershell
python -m demo.run_demo_scenarios
```

### Demonstration Summary Table
| Scenario ID | Project Description | Capacity | Roof & Tech Preference | Top International Match | Compatibility Score |
| :--- | :--- | :---: | :--- | :--- | :---: |
| **Scenario 1** | **Kothrud Housing Society** (Cooperative Housing Society common-lighting) | 35.0 kW | Flat RCC; String Inverters + TOPCon Modules | **SMA Solar Technology AG** *(Germany)* | **82.7 / 100** (`Strong Match`) |
| **Scenario 2** | **Baner Bungalow** (Individual Residential Bungalow with partial shading) | 6.0 kW | Flat RCC; Microinverters + Mono PERC | **Enphase Energy, Inc.** *(United States)* | **81.8 / 100** (`Strong Match`) |
| **Scenario 3** | **Hinjawadi IT Park** (Commercial IT Campus Rooftop Solar Installation) | 150.0 kW | Metal Shed; High-Efficiency String + TOPCon | **SMA Solar Technology AG** *(Germany)* | **82.7 / 100** (`Strong Match`) |

Sample generated reports are saved in [`demo/`](demo/):
- [`scenario_1_kothrud_chs_report.md`](demo/scenario_1_kothrud_chs_report.md)
- [`scenario_2_baner_bungalow_report.md`](demo/scenario_2_baner_bungalow_report.md)
- [`scenario_3_hinjawadi_commercial_report.md`](demo/scenario_3_hinjawadi_commercial_report.md)

---

## 🌐 7. Verified International Provider Registry

The active database includes verified international technology leaders with active India operations:

1. **SMA Solar Technology AG (Germany):** Premium string and central inverters, direct subsidiary in Mumbai, local Pune authorized service channel, dual BIS CRS & IEC compliance.
2. **Enphase Energy, Inc. (United States):** High-reliability microinverters, direct Bangalore subsidiary, Pune channel network, shade-resilient burst mode architecture.
3. **SolarEdge Technologies Inc. (Israel):** DC-optimized inverter architectures, rapid shutdown safety, direct India service presence.
4. **Sungrow Power Supply Co., Ltd. (China):** String inverters and C&I energy storage solutions, active manufacturing & warehousing in India.
5. **LONGi Green Energy Technology Co., Ltd. (China):** High-efficiency Hi-MO monocrystalline PERC and HPBC/TOPCon modules, BIS registered.
6. **Trina Solar Co., Ltd. (China):** Vertex S and Vertex S+ n-type TOPCon dual-glass rooftop modules up to 450W+, BIS CRS certified.

*All verified provider data are strictly segregated from synthetic fixtures via `is_sample_data: false`.*

---

## 🔒 8. Security & Secret Redaction Guarantee

- **Zero Secrets in Repository:** `.env` is permanently excluded via `.gitignore` and verified with `git check-ignore`.
- **Masked Display:** Keys are only shown in masked form (e.g., `mock-key-xxxx...yyyy`).
- **Log Stream Redaction:** `SanitizedFormatter` in `src/utils/logger.py` uses token regex matching to strip raw API keys from all logger outputs.
- **Automated Security Audit:** Integration test `test_security_audit_zero_secret_leak` ensures that exported reports never leak active credential strings.

---

## 📜 9. License & Academic Attribution
Developed as an applied AI engineering project under **United Nations Sustainable Development Goal 7, Target 7.A** (enhancing international cooperation to facilitate access to clean energy research and technology).
