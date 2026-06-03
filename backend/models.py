"""
Pydantic models for request/response schemas.
"""

from pydantic import BaseModel, Field
from typing import Optional


# ── Request Models ─────────────────────────────────────

class AnalyzeRequest(BaseModel):
    """User's free-text description for full analysis."""
    text: str = Field(
        ...,
        description="User's natural-language description of themselves",
        min_length=10,
        examples=[
            "I am a 20 year old female engineering student from Maharashtra. Family income is 4 lakh."
        ],
    )


class CompareRequest(BaseModel):
    """Compare two or more schemes by slug."""
    slugs: list[str] = Field(
        ...,
        min_length=2,
        description="Slugs of schemes to compare",
    )
    user_text: Optional[str] = Field(
        None,
        description="Optional user profile text for personalized comparison",
    )


class ChatRequest(BaseModel):
    """RAG-powered Q&A about schemes."""
    question: str = Field(
        ...,
        min_length=3,
        description="User's question about government schemes",
    )
    user_text: Optional[str] = Field(
        None,
        description="Optional user context for personalized answers",
    )


# ── Profile Model ─────────────────────────────────────

class UserProfile(BaseModel):
    """Structured profile extracted from user text."""
    state: Optional[str] = None
    income: Optional[float] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    education_level: Optional[str] = None
    course: Optional[str] = None
    year_of_study: Optional[int] = None
    cgpa: Optional[float] = None
    category: Optional[str] = None
    disability: bool = False
    minority: bool = False


# ── Eligibility Result ─────────────────────────────────

class EligibilityResult(BaseModel):
    """Result of eligibility check for a single scheme."""
    scheme_name: str
    slug: str
    eligible: bool
    match_score: float = Field(
        ..., ge=0, le=100,
        description="How well the user matches (0-100)",
    )
    rejection_reasons: list[str] = []
    matched_criteria: list[str] = []


# ── Document Check ─────────────────────────────────────

class DocumentCheck(BaseModel):
    """Document readiness for a scheme."""
    scheme_name: str
    required: list[str] = []
    common_documents: list[str] = []
    readiness_tip: str = ""


# ── Scheme Summary ─────────────────────────────────────

class SchemeSummary(BaseModel):
    """Scheme card shown in results."""
    scheme_name: str
    slug: str
    category: str = ""
    level: str = ""
    benefit_type: str = ""
    benefit_amount: Optional[float] = None
    score: float = 0
    match_score: float = 0
    tags: str = ""
    details_snippet: str = ""


# ── Full Analysis Response ─────────────────────────────

class AnalysisResponse(BaseModel):
    """Complete analysis result from the orchestrator."""
    profile: UserProfile
    total_schemes: int
    eligible_count: int
    potential_annual_benefit: float
    readiness_score: float
    eligible_schemes: list[SchemeSummary]
    top_rejection_reasons: list[str] = []
    document_checklist: list[DocumentCheck] = []
    guidance: str = ""


# ── Scheme Detail ──────────────────────────────────────

class SchemeDetail(BaseModel):
    """Full scheme information."""
    scheme_name: str
    slug: str
    details: str = ""
    benefits: str = ""
    eligibility: str = ""
    application: str = ""
    documents: str = ""
    level: str = ""
    category: str = ""
    tags: str = ""
    income_max: Optional[float] = None
    caste_category: Optional[str] = None
    disability_required: bool = False
    education_level: Optional[str] = None
    course: Optional[str] = None
    cgpa_min: Optional[float] = None
    benefit_type: str = ""
    benefit_amount: Optional[float] = None
    state: Optional[str] = None
    gender: Optional[str] = None


# ── Stats ──────────────────────────────────────────────

class StatsResponse(BaseModel):
    """Dashboard statistics."""
    total_schemes: int
    categories: dict[str, int]
    levels: dict[str, int]
    benefit_types: dict[str, int]
    avg_benefit_amount: float
    schemes_with_income_limit: int
