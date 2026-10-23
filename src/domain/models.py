"""
Domain data models for the International Solar Technology Partner Matching Agent.
Uses Pydantic v2 for robust data validation, type enforcement, and serialization.
"""

from datetime import date
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator


class BuildingType(str, Enum):
    RESIDENTIAL_INDIVIDUAL = "RESIDENTIAL_INDIVIDUAL"
    HOUSING_SOCIETY = "HOUSING_SOCIETY"
    COMMERCIAL = "COMMERCIAL"
    EDUCATIONAL = "EDUCATIONAL"
    INDUSTRIAL = "INDUSTRIAL"


class RoofType(str, Enum):
    RCC_FLAT = "RCC_FLAT"
    METAL_SHED = "METAL_SHED"
    TILED_SLOPE = "TILED_SLOPE"
    OPEN_TERRACE_MIXED = "OPEN_TERRACE_MIXED"


class TechType(str, Enum):
    MONO_PERC = "MONO_PERC"
    TOPCON = "TOPCON"
    HJT = "HJT"
    STRING_INVERTER = "STRING_INVERTER"
    MICROINVERTER = "MICROINVERTER"
    HYBRID_INVERTER = "HYBRID_INVERTER"
    BESS_LFP = "BESS_LFP"


class GridCoupling(str, Enum):
    ON_GRID_NET_METERED = "ON_GRID_NET_METERED"
    OFF_GRID = "OFF_GRID"
    HYBRID_STORAGE = "HYBRID_STORAGE"


class ServiceLevel(str, Enum):
    LOCAL_PUNE_OFFICE = "LOCAL_PUNE_OFFICE"
    MAHARASHTRA_SERVICE_NETWORK = "MAHARASHTRA_SERVICE_NETWORK"
    PAN_INDIA_AUTHORIZED_PARTNER = "PAN_INDIA_AUTHORIZED_PARTNER"
    REMOTE_INTERNATIONAL_SUPPORT = "REMOTE_INTERNATIONAL_SUPPORT"


class IndiaPresence(str, Enum):
    DIRECT_SUBSIDIARY = "DIRECT_SUBSIDIARY"
    AUTHORIZED_DISTRIBUTOR = "AUTHORIZED_DISTRIBUTOR"
    CERTIFIED_EPC_NETWORK = "CERTIFIED_EPC_NETWORK"
    IMPORT_ONLY_NO_LOCAL_OFFICE = "IMPORT_ONLY_NO_LOCAL_OFFICE"
    NONE = "NONE"


class CostTier(str, Enum):
    ECONOMY = "ECONOMY"
    MID_RANGE = "MID_RANGE"
    PREMIUM_TIER1 = "PREMIUM_TIER1"
    HIGH_END_SPECIALTY = "HIGH_END_SPECIALTY"


class SourceType(str, Enum):
    OFFICIAL_PORTAL = "OFFICIAL_PORTAL"
    PRODUCT_DATASHEET = "PRODUCT_DATASHEET"
    CERTIFICATION_BODY = "CERTIFICATION_BODY"
    GOVT_TENDER_RECORD = "GOVT_TENDER_RECORD"
    INDUSTRY_DIRECTORY = "INDUSTRY_DIRECTORY"


class EvidenceCitation(BaseModel):
    """Verifiable source citation proving provider claims and specifications."""
    citation_id: str = Field(..., description="Unique citation identifier")
    claim: str = Field(..., min_length=5, description="Factual technical or operational claim")
    source_url: HttpUrl = Field(..., description="Authenticated URL to manufacturer portal or datasheet")
    source_type: SourceType = Field(..., description="Authority classification of the source")
    last_verified: date = Field(..., description="Date the citation was validated")
    verification_note: Optional[str] = Field(default=None, description="Auditor notes or methodology")


class ProviderRecord(BaseModel):
    """Curated international solar technology provider profile with source attribution."""
    provider_id: str = Field(..., min_length=3, description="Unique slug or alphanumeric identifier")
    name: str = Field(..., min_length=2, description="Commercial brand or legal company name")
    headquarters_country: str = Field(..., min_length=2, description="Country of global headquarters")
    primary_technologies: List[TechType] = Field(..., min_length=1, description="Manufactured or supplied technologies")
    min_capacity_kw: float = Field(..., ge=0.1, description="Minimum viable project capacity supported in kW")
    max_capacity_kw: float = Field(..., ge=0.1, description="Maximum project capacity supported in kW")
    supported_building_types: List[BuildingType] = Field(..., min_length=1, description="Applicable building sectors")
    india_presence_type: IndiaPresence = Field(..., description="Structure of presence in Indian market")
    pune_service_availability: bool = Field(default=False, description="True if local Pune/PCMC channel or service exists")
    in_country_warehouse: bool = Field(default=False, description="True if spare parts warehouse exists in India")
    certifications: List[str] = Field(default_factory=list, description="BIS CRS, IEC, or UL compliance standards")
    warranty_terms: Dict[str, Any] = Field(default_factory=dict, description="Product and performance warranty parameters")
    estimated_cost_tier: CostTier = Field(default=CostTier.MID_RANGE, description="Relative cost classification")
    is_sample_data: bool = Field(default=False, description="Explicit flag: True if synthetic fixture, False if verified")
    last_audit_date: date = Field(..., description="Date of last data verification")
    evidence_records: List[EvidenceCitation] = Field(..., min_length=1, description="Mandatory list of verified citations")

    @model_validator(mode="after")
    def validate_capacity_bounds(self) -> "ProviderRecord":
        if self.min_capacity_kw > self.max_capacity_kw:
            raise ValueError(
                f"min_capacity_kw ({self.min_capacity_kw}) cannot exceed max_capacity_kw ({self.max_capacity_kw})"
            )
        return self


class ProjectProfile(BaseModel):
    """User-submitted rooftop solar project profile for Pune City."""
    project_id: str = Field(..., description="Unique identifier for the project inquiry")
    project_name: str = Field(..., min_length=3, max_length=100, description="Project identifier title")
    pune_locality: str = Field(..., min_length=2, description="Neighborhood in Pune/PCMC (e.g. Kothrud, Baner, PCMC)")
    building_type: BuildingType = Field(..., description="Sector category of the structure")
    target_capacity_kw: float = Field(..., ge=0.5, le=5000.0, description="Target solar capacity in kW")
    budget_inr: Optional[float] = Field(default=None, gt=0, description="Optional project budget in Indian Rupees")
    roof_type: RoofType = Field(..., description="Structural roof topology")
    technology_preference: List[TechType] = Field(..., min_length=1, description="Requested module, inverter, or battery technologies")
    grid_coupling: GridCoupling = Field(..., description="MSEDCL net metering or battery topology")
    service_requirement: ServiceLevel = Field(..., description="Minimum acceptable service footprint in Pune/India")
    priority_weights: Optional[Dict[str, float]] = Field(default=None, description="Optional custom criteria weights")

    @field_validator("pune_locality")
    @classmethod
    def clean_locality(cls, v: str) -> str:
        cleaned = v.strip().title()
        if len(cleaned) < 2:
            raise ValueError("Pune locality must contain at least 2 characters")
        return cleaned


class CompatibilityScore(BaseModel):
    """Detailed score breakdown across all six criteria defined in canonical knowledge."""
    total_score: float = Field(..., ge=0.0, le=100.0, description="Weighted aggregate compatibility score (0-100)")
    tech_fit: float = Field(..., ge=0.0, le=100.0, description="Technology alignment sub-score")
    capacity_fit: float = Field(..., ge=0.0, le=100.0, description="Operating scale match sub-score")
    service_fit: float = Field(..., ge=0.0, le=100.0, description="Local India/Pune presence sub-score")
    cert_fit: float = Field(..., ge=0.0, le=100.0, description="BIS and IEC certification sub-score")
    doc_fit: float = Field(..., ge=0.0, le=100.0, description="Evidence completeness and audit currency sub-score")
    cost_fit: float = Field(..., ge=0.0, le=100.0, description="Budget feasibility alignment sub-score")
    missing_penalty: float = Field(..., ge=0.0, le=25.0, description="Explicit deduction applied for unknown fields")
    score_tier: str = Field(..., description="Qualitative tier: Exceptional, Strong, Moderate, Low")


class MatchResult(BaseModel):
    """End-to-end matching evaluation for a single candidate provider."""
    provider: ProviderRecord = Field(..., description="Provider specification record")
    is_eligible: bool = Field(..., description="True if candidate passed all Stage 1 hard filters")
    disqualification_reasons: List[str] = Field(default_factory=list, description="Reasons for exclusion if ineligible")
    compatibility_score: Optional[CompatibilityScore] = Field(default=None, description="Stage 2 score if eligible")
    positive_drivers: List[str] = Field(default_factory=list, description="Primary positive score drivers")
    risk_flags: List[str] = Field(default_factory=list, description="Identified risks, caveats, or missing documentation")
    missing_fields: List[str] = Field(default_factory=list, description="List of unverified or missing parameters")
