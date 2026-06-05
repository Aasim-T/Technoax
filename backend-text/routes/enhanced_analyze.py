"""Enhanced text analysis endpoint with full trust intelligence pipeline.

Wraps the existing analysis pipeline and layers on:
- Social engineering detection
- Domain context classification
- Confidence scoring
- 4-tier risk classification
- AI probability signal breakdown
- Analytics tracking
- Analysis metadata

The original /analyze-text endpoint remains completely untouched.
"""

import logging
import time
from functools import lru_cache

from fastapi import APIRouter, Depends, HTTPException, status

from config.settings import Settings, get_settings
from models.request_models import AnalyzeTextRequest
from models.enhanced_response_models import (
    AnalysisMetadata,
    EnhancedAnalyzeTextResponse,
    SignalBreakdown,
    SocialEngineeringSignal,
)
from services.ai_probability_engine import AIProbabilityEngine
from services.analytics_tracker import AnalyticsTracker, get_analytics_tracker
from services.confidence_scorer import ConfidenceScorer
from services.context_analyzer import ContextAnalyzer
from services.explanation_engine import ExplanationEngine
from services.gemini_service import GeminiService, GeminiServiceError
from services.heatmap_builder import spans_to_heatmap, spans_to_matched_words
from services.manipulation_detector import ManipulationDetector
from services.resilient_client import get_gemini_circuit_breaker
from services.risk_classifier import EnhancedRiskClassifier
from services.social_engineering_detector import SocialEngineeringDetector
from services.trust_score import TrustScoreEngine

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Enhanced Analysis"])


# ── Dependency Injection ────────────────────────────────────────────────


def _get_manipulation_detector() -> ManipulationDetector:
    return ManipulationDetector()


def _get_trust_score_engine() -> TrustScoreEngine:
    return TrustScoreEngine()


@lru_cache
def _get_gemini_service() -> GeminiService:
    return GeminiService(get_settings())


def _get_explanation_engine() -> ExplanationEngine:
    return _ExplanationEngineProvider()


def _get_social_engineering_detector() -> SocialEngineeringDetector:
    return SocialEngineeringDetector()


def _get_context_analyzer() -> ContextAnalyzer:
    return ContextAnalyzer()


def _get_confidence_scorer() -> ConfidenceScorer:
    return ConfidenceScorer()


def _get_ai_probability_engine() -> AIProbabilityEngine:
    return AIProbabilityEngine()


def _get_risk_classifier() -> EnhancedRiskClassifier:
    return EnhancedRiskClassifier()


class _ExplanationEngineProvider(ExplanationEngine):
    """Explanation engine wired to cached Gemini service."""

    def __init__(self) -> None:
        super().__init__(_get_gemini_service())


# ── Enhanced Endpoint ───────────────────────────────────────────────────


@router.post(
    "/analyze-text/enhanced",
    response_model=EnhancedAnalyzeTextResponse,
    summary="Enhanced trust analysis with full intelligence pipeline",
    description=(
        "Runs the complete Technoax intelligence pipeline: manipulation detection, "
        "social engineering detection, domain classification, hybrid trust scoring, "
        "4-tier risk classification, confidence scoring, AI-generation probability "
        "with signal breakdown, and explainable AI reasoning."
    ),
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Invalid request payload"},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "Validation error"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Analysis failed"},
    },
)
async def enhanced_analyze_text(
    payload: AnalyzeTextRequest,
    detector: ManipulationDetector = Depends(_get_manipulation_detector),
    trust_engine: TrustScoreEngine = Depends(_get_trust_score_engine),
    gemini_service: GeminiService = Depends(_get_gemini_service),
    explanation_engine: ExplanationEngine = Depends(_get_explanation_engine),
    se_detector: SocialEngineeringDetector = Depends(_get_social_engineering_detector),
    context_analyzer: ContextAnalyzer = Depends(_get_context_analyzer),
    confidence_scorer: ConfidenceScorer = Depends(_get_confidence_scorer),
    ai_engine: AIProbabilityEngine = Depends(_get_ai_probability_engine),
    risk_classifier: EnhancedRiskClassifier = Depends(_get_risk_classifier),
    analytics: AnalyticsTracker = Depends(get_analytics_tracker),
) -> EnhancedAnalyzeTextResponse:
    """Enhanced text analysis with full Technoax intelligence pipeline."""
    start_time = time.time()

    try:
        text = payload.text
        word_count = len(text.split())

        # ── Stage 1: Primary Manipulation Detection (existing pipeline) ──
        detection = detector.detect(text)
        rule_score, _, _ = trust_engine.calculate(
            detection.detected_patterns,
            detection.spans,
        )

        # ── Stage 2: Social Engineering Detection ──
        se_result = se_detector.detect(text)

        # ── Stage 3: Domain Classification ──
        domain_ctx = context_analyzer.classify_domain(text)

        # ── Stage 4: Gemini Hybrid Scoring ──
        final_score = rule_score
        gemini_score: int | None = None
        gemini_used = False
        circuit_state = "closed"

        circuit_breaker = get_gemini_circuit_breaker()
        circuit_state = circuit_breaker.state.value

        if gemini_service.is_available:
            try:
                gemini_call_start = time.time()
                gemini_analysis = gemini_service.generate_trust_analysis(text)
                gemini_call_latency = (time.time() - gemini_call_start) * 1000

                gemini_score = gemini_analysis.trust_score
                final_score = trust_engine.compute_hybrid_score(
                    rule_score=rule_score,
                    gemini_score=gemini_score,
                )
                gemini_used = True
                analytics.record_gemini_call(success=True, latency_ms=gemini_call_latency)
                await circuit_breaker.record_success()

                logger.info(
                    "Enhanced: Gemini trust OK — rule=%s gemini=%s final=%s",
                    rule_score, gemini_score, final_score,
                )
            except GeminiServiceError as exc:
                analytics.record_gemini_call(success=False)
                await circuit_breaker.record_failure(exc)
                logger.warning(
                    "Enhanced: Gemini trust unavailable — fallback to rule-based: %s",
                    exc,
                )

        risk_level, trust_meter = trust_engine.derive_from_score(final_score)

        # ── Stage 5: Heatmap + Matched Words ──
        matched_words = spans_to_matched_words(detection.spans)
        manipulation_heatmap = spans_to_heatmap(detection.spans)

        # ── Stage 6: Explainability ──
        ai_explanation, recommendation = explanation_engine.build_explainability(
            text=text,
            detected_patterns=detection.detected_patterns,
            matched_words=matched_words,
            trust_score=final_score,
            trust_meter=trust_meter.value,
            risk_level=risk_level.value,
        )

        # ── Stage 7: AI Probability (Rule-Based Statistical) ──
        ai_prob_result = ai_engine.compute_rule_based_probability(text)
        rule_ai_probability = ai_prob_result.probability

        # ── Stage 8: AI Probability (Gemini Hybrid) ──
        ai_generated_probability = rule_ai_probability
        ai_generation_explanation = ai_prob_result.reasoning

        if gemini_service.is_available:
            try:
                ai_generation = gemini_service.generate_ai_probability_analysis(text)
                gemini_ai_prob = ai_generation.ai_generated_probability
                ai_generated_probability = ai_engine.compute_hybrid_probability(
                    rule_score=rule_ai_probability,
                    gemini_score=gemini_ai_prob,
                )
                ai_generation_explanation = ai_generation.ai_generation_explanation
                logger.info(
                    "Enhanced: AI prob — rule=%s gemini=%s hybrid=%s",
                    rule_ai_probability, gemini_ai_prob, ai_generated_probability,
                )
            except GeminiServiceError as exc:
                logger.warning(
                    "Enhanced: Gemini AI probability unavailable — using rule-based: %s",
                    exc,
                )

        # ── Stage 9: Confidence Scoring ──
        confidence = confidence_scorer.compute(
            text=text,
            detected_pattern_count=len(detection.detected_patterns),
            matched_word_count=len(detection.spans),
            rule_score=rule_score,
            gemini_score=gemini_score,
        )

        # ── Stage 10: Enhanced Risk Classification (4-tier) ──
        enhanced_risk = risk_classifier.classify(
            trust_score=final_score,
            detected_patterns=detection.detected_patterns,
            social_engineering_categories=se_result.detected_categories,
            domain=domain_ctx.domain,
            matched_word_count=len(detection.spans) + se_result.signal_count,
            text_word_count=word_count,
        )

        # ── Stage 11: Build Response ──
        elapsed_ms = (time.time() - start_time) * 1000

        # Social engineering signals for response
        se_signals = [
            SocialEngineeringSignal(
                word=s.word,
                category=s.category,
                severity=s.severity,
                start_index=s.start_index,
                end_index=s.end_index,
            )
            for s in se_result.spans
        ]

        # AI probability breakdown
        ai_breakdown = [
            SignalBreakdown(
                name=s.name,
                score=s.score,
                weight=s.weight,
                reasoning=s.reasoning,
            )
            for s in ai_prob_result.signals
        ]

        # Analysis metadata
        metadata = AnalysisMetadata(
            analysis_duration_ms=round(elapsed_ms, 1),
            engine_version="2.0.0",
            gemini_available=gemini_service.is_available,
            gemini_used=gemini_used,
            circuit_breaker_state=circuit_state,
            rule_score=rule_score,
            gemini_score=gemini_score,
            prompt_template_version="v2",
        )

        # Record analytics
        analytics.record_analysis(
            trust_score=final_score,
            risk_level=enhanced_risk.level.value,
            detected_patterns=detection.detected_patterns + se_result.detected_categories,
            matched_word_count=len(detection.spans) + se_result.signal_count,
            domain=domain_ctx.domain.value,
            confidence_score=confidence.confidence_score,
            ai_probability=ai_generated_probability,
            text_length=len(text),
            gemini_used=gemini_used,
            latency_ms=elapsed_ms,
        )

        return EnhancedAnalyzeTextResponse(
            # Original fields (backward compatible)
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
            # Enhanced fields
            confidence_score=confidence.confidence_score,
            confidence_label=confidence.confidence_label,
            confidence_reasoning=confidence.reasoning,
            domain_context=domain_ctx.domain.value,
            domain_confidence=domain_ctx.confidence,
            domain_indicators=domain_ctx.matched_indicators,
            enhanced_risk_level=enhanced_risk.level.value,
            enhanced_risk_description=enhanced_risk.description,
            threat_indicators=enhanced_risk.threat_indicators,
            social_engineering_signals=se_signals,
            social_engineering_categories=se_result.detected_categories,
            ai_probability_breakdown=ai_breakdown,
            rule_based_ai_probability=rule_ai_probability,
            analysis_metadata=metadata,
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Enhanced analysis failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Enhanced text analysis failed: {exc}",
        ) from exc
