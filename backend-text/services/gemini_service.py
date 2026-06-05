"""Reusable Google Gemini API integration via the google-genai SDK."""

import json
import logging
from typing import Any, TypeVar

from google import genai
from google.genai import types
from google.genai.errors import APIError
from pydantic import BaseModel, Field, ValidationError

from config.settings import Settings
from models.response_models import MatchedWord

logger = logging.getLogger(__name__)

# Module-level singleton client (cached by API key)
_cached_client: genai.Client | None = None
_cached_api_key: str | None = None

TModel = TypeVar("TModel", bound=BaseModel)


class GeminiTrustAnalysis(BaseModel):
    """Contextual trust score and rationale returned by Gemini for hybrid scoring."""

    trust_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Gemini-estimated contextual trustworthiness from 0 to 100",
    )
    explanation: str = Field(
        description="Concise explanation of contextual trustworthiness",
    )
    recommendation: str = Field(
        description="Actionable recommendation based on contextual trust analysis",
    )


class AIGenerationAnalysis(BaseModel):
    """Probability estimate of whether content appears AI-generated."""

    ai_generated_probability: int = Field(
        ...,
        ge=0,
        le=100,
        description="Estimated probability (0-100) that content was AI-generated",
    )
    ai_generation_explanation: str = Field(
        description=(
            "Explainable rationale describing linguistic patterns and which parts "
            "appear likely AI-generated"
        ),
    )


class GeminiInsight(BaseModel):
    """Structured explainability payload returned by Gemini."""

    ai_explanation: str = Field(
        description=(
            "Professional explanation: manipulation reasoning, psychological tactics, "
            "and contextual trust impact"
        ),
    )
    recommendation: str = Field(
        description="Verification recommendation and reader guidance",
    )


class GeminiServiceError(Exception):
    """Raised when Gemini API calls fail."""

    def __init__(self, message: str, *, cause: Exception | None = None) -> None:
        super().__init__(message)
        self.cause = cause


class GeminiService:
    """Wrapper around the Google GenAI SDK for Technoax hybrid trust intelligence."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    @property
    def is_available(self) -> bool:
        """Whether Gemini API key is configured."""
        return self._settings.is_gemini_configured

    def _get_client(self) -> genai.Client:
        """
        Return a cached singleton Gemini client for the configured API key.

        Uses: genai.Client(api_key=settings.gemini_api_key)
        """
        global _cached_client, _cached_api_key

        api_key = self._settings.gemini_api_key
        if not api_key:
            raise GeminiServiceError(
                "GEMINI_API_KEY is not configured. Set it in backend/.env."
            )

        if _cached_client is None or _cached_api_key != api_key:
            logger.info("Initializing Gemini client (model=%s)", self._settings.gemini_model)
            _cached_client = genai.Client(api_key=api_key)
            _cached_api_key = api_key

        return _cached_client

    def generate_trust_analysis(self, text: str) -> GeminiTrustAnalysis:
        """
        Contextual trust scoring for hybrid blending (70% rule / 30% Gemini).

        Analyzes manipulation intensity, emotional persuasion, and trustworthiness.
        """
        try:
            return self._generate_structured(
                prompt=self._build_trust_analysis_prompt(text),
                schema_model=GeminiTrustAnalysis,
                temperature=0.2,
                error_context="contextual trust analysis",
            )
        except GeminiServiceError:
            raise
        except APIError as exc:
            logger.warning("Gemini trust analysis API error: %s", exc)
            raise GeminiServiceError(
                "Failed to generate contextual trust analysis", cause=exc
            ) from exc
        except Exception as exc:
            logger.exception("Unexpected Gemini trust analysis failure")
            raise GeminiServiceError(
                "Failed to generate contextual trust analysis", cause=exc
            ) from exc

    def generate_ai_probability_analysis(self, text: str) -> AIGenerationAnalysis:
        """
        Estimate whether content appears AI-generated with explainable reasoning.

        Returns a probability (0-100), not a certainty claim.
        """
        try:
            return self._generate_structured(
                prompt=self._build_ai_generation_prompt(text),
                schema_model=AIGenerationAnalysis,
                temperature=0.2,
                error_context="AI generation probability analysis",
            )
        except GeminiServiceError:
            raise
        except APIError as exc:
            logger.warning("Gemini AI generation analysis API error: %s", exc)
            raise GeminiServiceError(
                "Failed to generate AI probability analysis", cause=exc
            ) from exc
        except Exception as exc:
            logger.exception("Unexpected Gemini AI generation analysis failure")
            raise GeminiServiceError(
                "Failed to generate AI probability analysis", cause=exc
            ) from exc

    def generate_insight(
        self,
        text: str,
        detected_patterns: list[str],
        matched_words: list[MatchedWord],
        trust_score: int,
        trust_meter: str,
        risk_level: str,
    ) -> GeminiInsight:
        """Professional AI explainability for trust intelligence responses."""
        try:
            return self._generate_structured(
                prompt=self._build_insight_prompt(
                    text=text,
                    detected_patterns=detected_patterns,
                    matched_words=matched_words,
                    trust_score=trust_score,
                    trust_meter=trust_meter,
                    risk_level=risk_level,
                ),
                schema_model=GeminiInsight,
                temperature=0.25,
                error_context="AI explainability insight",
            )
        except GeminiServiceError:
            raise
        except APIError as exc:
            logger.warning("Gemini explainability API error: %s", exc)
            raise GeminiServiceError("Failed to generate AI insight", cause=exc) from exc
        except Exception as exc:
            logger.exception("Unexpected Gemini explainability failure")
            raise GeminiServiceError("Failed to generate AI insight", cause=exc) from exc

    def _generate_structured(
        self,
        prompt: str,
        schema_model: type[TModel],
        temperature: float,
        error_context: str,
    ) -> TModel:
        """Call Gemini with JSON schema enforcement and validate the response."""
        client = self._get_client()

        response = client.models.generate_content(
            model=self._settings.gemini_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=temperature,
                response_mime_type="application/json",
                response_schema=schema_model,
            ),
        )

        raw = response.text
        if not raw:
            raise GeminiServiceError(f"Gemini returned an empty response for {error_context}")

        return self._parse_json(raw, schema_model, error_context)

    @staticmethod
    def _parse_json(raw: str, schema_model: type[TModel], error_context: str) -> TModel:
        try:
            payload: dict[str, Any] = json.loads(raw)
            return schema_model.model_validate(payload)
        except (json.JSONDecodeError, ValidationError) as exc:
            raise GeminiServiceError(
                f"Gemini {error_context} could not be parsed as valid JSON"
            ) from exc

    @staticmethod
    def _build_trust_analysis_prompt(text: str) -> str:
        return f"""You are Technoax, an explainable digital trust intelligence system.

Analyze the following content and estimate its trustworthiness.

Evaluate:

* emotional manipulation
* fear tactics
* urgency tactics
* clickbait
* conspiracy framing
* misleading persuasion
* suspicious framing
* psychological pressure

Provide:

1. trust_score (0-100)
2. concise explanation
3. recommendation

Scoring guidance:

* Highly manipulative content → low score
* Neutral informational content → high score

Return ONLY valid JSON.

Content:
\"\"\"
{text[:8000]}
\"\"\"
"""

    @staticmethod
    def _build_ai_generation_prompt(text: str) -> str:
        return f"""You are Technoax AI-authenticity engine.

Analyze whether the following content appears AI-generated.

Evaluate:

* repetitive structure
* excessive consistency
* overly polished language
* generic phrasing
* low burstiness
* formal AI-like sentence patterns
* LLM-style wording

Return ONLY valid JSON.

JSON format:

{{
  "ai_generated_probability": integer,
  "ai_generation_explanation": "string"
}}

Probability rules:

0-20:
Likely human-written

21-50:
Possibly AI-assisted

51-80:
Strong AI indicators

81-100:
Highly likely AI-generated

Content:
\"\"\"
{text[:8000]}
\"\"\"
"""

    @staticmethod
    def _build_insight_prompt(
        text: str,
        detected_patterns: list[str],
        matched_words: list[MatchedWord],
        trust_score: int,
        trust_meter: str,
        risk_level: str,
    ) -> str:
        patterns_str = ", ".join(detected_patterns) if detected_patterns else "none"
        words_str = json.dumps(
            [w.model_dump() for w in matched_words],
            ensure_ascii=False,
        )

        return f"""You are Technoax, a senior explainable digital trust intelligence analyst.

Produce a professional trust briefing for the content below.

Rule-based signals (authoritative — do not contradict):
- Hybrid trust score: {trust_score}/100
- Trust meter: {trust_meter}
- Risk level: {risk_level}
- Detected categories: {patterns_str}
- Matched manipulation words: {words_str}

Content:
\"\"\"
{text[:8000]}
\"\"\"

Return JSON with:

1) ai_explanation — One cohesive paragraph (3–5 sentences) covering:
   • Why the content feels manipulative or trustworthy
   • Psychological tactics (fear, urgency, outrage, conspiracy framing, social proof pressure)
   • Why audiences may emotionally believe or share it
   • Contextual trust impact given detected signals

2) recommendation — One or two sentences of verification guidance.
   CRITICAL RULES for recommendation:
   • NEVER write "verification is not advised", "no verification needed", or any equivalent phrase suggesting verification is unnecessary.
   • For high-trust content (score >= 80): use exactly — "No major manipulation indicators were detected. However, important factual claims should still be verified using reliable sources when accuracy is critical."
   • For medium-trust content (score 50–79): advise verifying key claims against primary sources before relying on the content.
   • For low-trust content (score < 50): advise treating claims as unverified and seeking corroboration from independent, reputable sources before sharing or acting.

Style:
- Concise, professional, explainable — not generic chatbot language
- Evidence-oriented; reference detected patterns when present
- Avoid: "As an AI", "In conclusion", "It's important to note"
"""
