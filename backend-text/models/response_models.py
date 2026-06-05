"""Response models for Technoax API."""

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    """Trust risk classification."""

    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class TrustMeter(str, Enum):
    """Human-readable trust meter derived from trust score."""

    HIGH_TRUST = "High Trust"
    MODERATE_TRUST = "Moderate Trust"
    LOW_TRUST = "Low Trust"


class SeverityLevel(str, Enum):
    """Manipulation signal severity for heatmap visualization."""

    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class MatchedWord(BaseModel):
    """A detected manipulation keyword with category and severity."""

    word: str = Field(..., description="Matched substring from the analyzed text")
    category: str = Field(
        ...,
        description="Manipulation category (Fear, Urgency, Clickbait, etc.)",
    )
    severity: str = Field(
        ...,
        description="Severity tier for UI emphasis",
        examples=["Medium"],
    )


class HeatmapWord(MatchedWord):
    """Manipulation match with character offsets for frontend heatmap highlighting."""

    start_index: int = Field(
        ...,
        ge=0,
        description="Inclusive start character index in the source text",
    )
    end_index: int = Field(
        ...,
        ge=0,
        description="Exclusive end character index in the source text",
    )


class AnalyzeTextResponse(BaseModel):
    """Enhanced trust analysis result with explainability and heatmap support."""

    trust_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Digital trust score from 0 (untrustworthy) to 100 (trustworthy)",
        examples=[42],
    )
    trust_meter: str = Field(
        ...,
        description="Human-readable trust meter label",
        examples=["Low Trust"],
    )
    risk_level: str = Field(
        ...,
        description="Risk tier derived from trust score",
        examples=["High"],
    )
    detected_patterns: list[str] = Field(
        ...,
        description="Manipulation categories detected in the text",
        examples=[["Fear", "Urgency"]],
    )
    matched_words: list[MatchedWord] = Field(
        default_factory=list,
        description="Word-level manipulation matches with severity",
    )
    manipulation_heatmap: list[HeatmapWord] = Field(
        default_factory=list,
        description="Character-indexed matches for frontend heatmap rendering",
    )
    ai_explanation: str = Field(
        ...,
        description="Professional AI explanation of manipulation tactics and trust signals",
    )
    recommendation: str = Field(
        ...,
        description="Actionable guidance on whether and how to verify the content",
    )
    ai_generated_probability: int = Field(
        ...,
        ge=0,
        le=100,
        description="Estimated probability (0-100) that the content was AI-generated",
        examples=[86],
    )
    ai_generation_explanation: str = Field(
        ...,
        description=(
            "Explainable analysis of linguistic patterns suggesting AI-generated content"
        ),
        examples=[
            "The text exhibits unusually consistent sentence structure and polished phrasing "
            "commonly associated with large language model outputs."
        ],
    )


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(default="ok")
    service: str = Field(default="Technoax")
    version: str
