"""Produces AI explanations and verification recommendations for trust analysis."""

import logging

from models.response_models import MatchedWord
from services.gemini_service import GeminiInsight, GeminiService, GeminiServiceError

logger = logging.getLogger(__name__)


class ExplanationEngine:
    """Generates ai_explanation and recommendation fields for API responses."""

    def __init__(self, gemini_service: GeminiService) -> None:
        self._gemini = gemini_service

    def build_explainability(
        self,
        text: str,
        detected_patterns: list[str],
        matched_words: list[MatchedWord],
        trust_score: int,
        trust_meter: str,
        risk_level: str,
    ) -> tuple[str, str]:
        """
        Return (ai_explanation, recommendation) using Gemini or rule-based fallback.
        """
        if not self._gemini.is_available:
            logger.warning("GEMINI_API_KEY not configured — using rule-based explainability")
            return self._fallback_explainability(
                detected_patterns=detected_patterns,
                matched_words=matched_words,
                trust_score=trust_score,
                trust_meter=trust_meter,
                risk_level=risk_level,
            )

        try:
            insight = self._gemini.generate_insight(
                text=text,
                detected_patterns=detected_patterns,
                matched_words=matched_words,
                trust_score=trust_score,
                trust_meter=trust_meter,
                risk_level=risk_level,
            )
            logger.info("Gemini explainability generated successfully")
            return insight.ai_explanation, insight.recommendation
        except GeminiServiceError as exc:
            logger.warning("Gemini explainability unavailable; using fallback: %s", exc)
            return self._fallback_explainability(
                detected_patterns=detected_patterns,
                matched_words=matched_words,
                trust_score=trust_score,
                trust_meter=trust_meter,
                risk_level=risk_level,
            )

    @staticmethod
    def _fallback_explainability(
        detected_patterns: list[str],
        matched_words: list[MatchedWord],
        trust_score: int,
        trust_meter: str,
        risk_level: str,
    ) -> tuple[str, str]:
        if not detected_patterns:
            explanation = (
                f"This content registers a trust score of {trust_score}/100 ({trust_meter}) "
                f"with {risk_level} risk. Rule-based scanning found no fear, urgency, clickbait, "
                "emotional trigger, or conspiracy keywords. The language appears "
                "relatively neutral based on deterministic analysis."
            )
            recommendation = (
                "No major manipulation indicators were detected. However, important factual "
                "claims should still be verified using reliable sources when accuracy is critical."
            )
            return explanation, recommendation

        word_details = ", ".join(
            f'"{m.word}" ({m.category}, {m.severity})' for m in matched_words
        )
        patterns_line = ", ".join(detected_patterns)

        explanation = (
            f"Scored {trust_score}/100 ({trust_meter}, {risk_level} risk). "
            f"Detected categories: {patterns_line}. "
            f"Matched signals: {word_details}. "
            "These patterns commonly exploit urgency, fear, or sensational framing to influence "
            "belief before verification."
        )

        if trust_score < 50:
            recommendation = (
                "Treat claims as unverified. Seek corroboration from independent, reputable sources "
                "before sharing or acting on this content."
            )
        elif trust_score < 80:
            recommendation = (
                "Verify key claims against primary sources before relying on this content for decisions."
            )
        else:
            recommendation = (
                "No major manipulation indicators were detected. However, important factual "
                "claims should still be verified using reliable sources when accuracy is critical."
            )

        return explanation, recommendation
