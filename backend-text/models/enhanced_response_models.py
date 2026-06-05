"""Enhanced response models for the /analyze-text/enhanced endpoint.

Extends the existing AnalyzeTextResponse with additional intelligence fields
while maintaining full backward compatibility.
"""

from pydantic import BaseModel, Field

from models.response_models import AnalyzeTextResponse


class SignalBreakdown(BaseModel):
    """Individual AI probability sub-signal score."""

    name: str = Field(..., description="Signal name (e.g., Burstiness, Vocabulary Richness)")
    score: int = Field(..., ge=0, le=100, description="Sub-signal score (0-100)")
    weight: float = Field(..., description="Contribution weight to composite score")
    reasoning: str = Field(..., description="Human-readable explanation of this signal")


class SocialEngineeringSignal(BaseModel):
    """A detected social engineering manipulation signal."""

    word: str = Field(..., description="Matched phrase from the text")
    category: str = Field(..., description="Social engineering sub-category")
    severity: str = Field(..., description="Signal severity (Low/Medium/High)")
    start_index: int = Field(..., ge=0, description="Start character offset")
    end_index: int = Field(..., ge=0, description="End character offset")


class AnalysisMetadata(BaseModel):
    """Metadata about the analysis execution."""

    analysis_duration_ms: float = Field(
        ..., description="Total analysis time in milliseconds"
    )
    engine_version: str = Field(
        default="2.0.0", description="Analysis engine version"
    )
    gemini_available: bool = Field(
        ..., description="Whether Gemini was available for this analysis"
    )
    gemini_used: bool = Field(
        ..., description="Whether Gemini was successfully used"
    )
    circuit_breaker_state: str = Field(
        default="closed", description="Current Gemini circuit breaker state"
    )
    rule_score: int = Field(
        ..., ge=0, le=100, description="Raw rule-based trust score before hybrid blending"
    )
    gemini_score: int | None = Field(
        default=None, description="Gemini contextual trust score (null if unavailable)"
    )
    prompt_template_version: str = Field(
        default="v2", description="Prompt template version used"
    )


class EnhancedAnalyzeTextResponse(AnalyzeTextResponse):
    """
    Enhanced trust analysis response with extended intelligence.

    Inherits all fields from AnalyzeTextResponse and adds:
    - Confidence scoring
    - Domain context classification
    - 4-tier risk classification
    - Social engineering detection
    - AI probability signal breakdown
    - Analysis metadata
    """

    # Confidence scoring
    confidence_score: int = Field(
        default=0,
        ge=0,
        le=100,
        description="System confidence in its own analysis (0-100)",
    )
    confidence_label: str = Field(
        default="Moderate",
        description="Confidence tier (Very High / High / Moderate / Low)",
    )
    confidence_reasoning: str = Field(
        default="",
        description="Explanation of confidence factors",
    )

    # Domain context
    domain_context: str = Field(
        default="General",
        description="Classified content domain (Medical / Financial / Political / General)",
    )
    domain_confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence in domain classification (0.0-1.0)",
    )
    domain_indicators: list[str] = Field(
        default_factory=list,
        description="Domain-specific keywords that triggered classification",
    )

    # Enhanced risk classification (4-tier)
    enhanced_risk_level: str = Field(
        default="Low Risk",
        description="4-tier risk classification (Low/Medium/High/Critical Risk)",
    )
    enhanced_risk_description: str = Field(
        default="",
        description="Detailed risk assessment description",
    )
    threat_indicators: list[str] = Field(
        default_factory=list,
        description="List of identified threat indicators",
    )

    # Social engineering detection
    social_engineering_signals: list[SocialEngineeringSignal] = Field(
        default_factory=list,
        description="Detected social engineering manipulation patterns",
    )
    social_engineering_categories: list[str] = Field(
        default_factory=list,
        description="Unique social engineering categories detected",
    )

    # AI probability breakdown
    ai_probability_breakdown: list[SignalBreakdown] = Field(
        default_factory=list,
        description="Per-signal AI generation detection scores",
    )
    rule_based_ai_probability: int = Field(
        default=0,
        ge=0,
        le=100,
        description="Rule-based statistical AI probability (independent of Gemini)",
    )

    # Analysis metadata
    analysis_metadata: AnalysisMetadata | None = Field(
        default=None,
        description="Execution metadata including timing and engine state",
    )
