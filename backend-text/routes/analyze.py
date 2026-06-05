"""Text analysis API routes."""

import logging
from functools import lru_cache

from fastapi import APIRouter, Depends, HTTPException, status

from config.settings import Settings, get_settings
from models.request_models import AnalyzeTextRequest
from models.response_models import AnalyzeTextResponse
from services.ai_probability_engine import AIProbabilityEngine
from services.explanation_engine import ExplanationEngine
from services.gemini_service import GeminiService, GeminiServiceError
from services.heatmap_builder import spans_to_heatmap, spans_to_matched_words
from services.manipulation_detector import ManipulationDetector
from services.trust_score import TrustScoreEngine

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Analysis"])


def get_manipulation_detector() -> ManipulationDetector:
    return ManipulationDetector()


def get_trust_score_engine() -> TrustScoreEngine:
    return TrustScoreEngine()


@lru_cache
def get_gemini_service() -> GeminiService:
    """Cached Gemini service singleton (reuses client across requests)."""
    return GeminiService(get_settings())


def get_explanation_engine() -> ExplanationEngine:
    return ExplanationEngine(get_gemini_service())


def get_ai_probability_engine() -> AIProbabilityEngine:
    return AIProbabilityEngine()


@router.post(
    "/analyze-text",
    response_model=AnalyzeTextResponse,
    summary="Analyze text for manipulation and trustworthiness",
    description=(
        "Runs manipulation detection, hybrid trust scoring, AI-generation probability analysis, "
        "heatmap indices, and explainable AI reasoning."
    ),
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Invalid request payload"},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "Validation error"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Analysis failed"},
    },
)
async def analyze_text(
    payload: AnalyzeTextRequest,
    detector: ManipulationDetector = Depends(get_manipulation_detector),
    trust_engine: TrustScoreEngine = Depends(get_trust_score_engine),
    gemini_service: GeminiService = Depends(get_gemini_service),
    explanation_engine: ExplanationEngine = Depends(get_explanation_engine),
    ai_engine: AIProbabilityEngine = Depends(get_ai_probability_engine),
) -> AnalyzeTextResponse:
    """Analyze submitted text and return enhanced trust assessment."""
    try:
        detection = detector.detect(payload.text)
        rule_score, _, _ = trust_engine.calculate(
            detection.detected_patterns,
            detection.spans,
        )

        final_score = rule_score
        gemini_score: int | None = None

        if gemini_service.is_available:
            try:
                gemini_analysis = gemini_service.generate_trust_analysis(payload.text)
                gemini_score = gemini_analysis.trust_score
                final_score = trust_engine.compute_hybrid_score(
                    rule_score=rule_score,
                    gemini_score=gemini_score,
                )
                logger.info(
                    "Gemini trust analysis OK — rule=%s gemini=%s final=%s",
                    rule_score,
                    gemini_score,
                    final_score,
                )
            except GeminiServiceError as exc:
                logger.warning(
                    "Gemini contextual trust analysis unavailable; using rule-based score only: %s",
                    exc,
                )
        else:
            logger.warning("GEMINI_API_KEY not configured — hybrid scoring disabled")

        # Temporary debug logging for hybrid score testing
        print("RULE SCORE:", rule_score)
        print("GEMINI SCORE:", gemini_score if gemini_score is not None else "N/A (fallback)")
        print("FINAL SCORE:", final_score)

        risk_level, trust_meter = trust_engine.derive_from_score(final_score)

        matched_words = spans_to_matched_words(detection.spans)
        manipulation_heatmap = spans_to_heatmap(detection.spans)

        ai_explanation, recommendation = explanation_engine.build_explainability(
            text=payload.text,
            detected_patterns=detection.detected_patterns,
            matched_words=matched_words,
            trust_score=final_score,
            trust_meter=trust_meter.value,
            risk_level=risk_level.value,
        )

        # ── AI Probability (Rule-Based Statistical) ──
        ai_prob_result = ai_engine.compute_rule_based_probability(payload.text)
        rule_ai_probability = ai_prob_result.probability

        # ── AI Probability (Gemini Hybrid) ──
        ai_generated_probability = rule_ai_probability
        ai_generation_explanation = ai_prob_result.reasoning

        if gemini_service.is_available:
            try:
                ai_generation = gemini_service.generate_ai_probability_analysis(payload.text)
                gemini_ai_prob = ai_generation.ai_generated_probability
                ai_generated_probability = ai_engine.compute_hybrid_probability(
                    rule_score=rule_ai_probability,
                    gemini_score=gemini_ai_prob,
                )
                ai_generation_explanation = ai_generation.ai_generation_explanation
                logger.info(
                    "Gemini AI generation analysis OK — probability=%s",
                    ai_generated_probability,
                )
            except GeminiServiceError as exc:
                logger.warning(
                    "Gemini AI generation analysis unavailable; using fallback: %s",
                    exc,
                )

        return AnalyzeTextResponse(
            trust_score=final_score,
            trust_meter=trust_meter.value,
            risk_level=risk_level.value,
            detected_patterns=detection.detected_patterns,
            matched_words=matched_words,
            manipulation_heatmap=manipulation_heatmap,
            ai_explanation=ai_explanation,
            recommendation=recommendation,
            ai_generated_probability=ai_generated_probability,
            ai_generation_explanation=ai_generation_explanation,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Text analysis failed: {exc}",
        ) from exc
