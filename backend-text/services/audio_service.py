"""Audio Authenticity Intelligence Engine — Full Pipeline Orchestrator.

This service orchestrates the complete audio analysis pipeline:

  Phase 1 — Speech-to-Text (faster-whisper)
  Phase 2 — Audio Feature Extraction (librosa)
  Phase 3 — AI Audio Detection (heuristic scoring)
  Phase 4 — Gemini Explainability
  Phase 5 — Transcript Trust Analysis (reuse existing engines)

IMPORTANT: This module ONLY READS from existing Technoax services.
It does NOT modify any existing service, route, or model.

Existing services reused (imported, not copied):
  - ManipulationDetector        → detect manipulation patterns in transcript
  - TrustScoreEngine            → compute trust score from patterns
  - AIProbabilityEngine         → estimate AI-generated probability of transcript
  - GeminiService               → generate audio explainability via Gemini
  - heatmap_builder             → convert spans to matched words
"""

import logging
import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from pydantic import BaseModel, Field

from config.settings import Settings
from schemas.audio_schema import AudioAnalysisResponse, TranscriptAnalysis
from services.ai_probability_engine import AIProbabilityEngine
from services.audio_detector import AudioAIDetector
from services.audio_features import AudioFeatureExtractor
from services.gemini_service import GeminiService, GeminiServiceError
from services.heatmap_builder import spans_to_matched_words
from services.manipulation_detector import ManipulationDetector
from services.trust_score import TrustScoreEngine

logger = logging.getLogger(__name__)

# ── Whisper model size (overrideable via WHISPER_MODEL env var) ─────────────
_DEFAULT_WHISPER_MODEL = "tiny"


# ── Gemini structured schema for audio explainability ───────────────────────

class AudioGeminiExplanation(BaseModel):
    """Structured Gemini response for audio authenticity explainability."""

    audio_explanation: str = Field(
        description=(
            "One paragraph (3-5 sentences) explaining why the audio was classified "
            "as human or AI generated, referencing the specific acoustic indicators."
        )
    )
    confidence_explanation: str = Field(
        description=(
            "One sentence explaining the confidence level of the classification."
        )
    )
    additional_indicators: list[str] = Field(
        default_factory=list,
        description="Any additional acoustic indicators Gemini identifies beyond the rule-based list.",
    )


# ── Speech-to-Text result ────────────────────────────────────────────────────

@dataclass
class WhisperResult:
    """Result from faster-whisper transcription."""

    transcript: str
    language: str
    language_probability: float
    duration_seconds: float


class AudioServiceError(Exception):
    """Raised when the audio analysis pipeline fails irrecoverably."""

    def __init__(self, message: str, http_status: int = 500) -> None:
        super().__init__(message)
        self.http_status = http_status


class AudioService:
    """
    Orchestrates the full Audio Authenticity Intelligence Engine pipeline.

    Designed to be instantiated once (as a FastAPI dependency) and reused
    across requests. All heavy models (Whisper) are loaded lazily on first use.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._whisper_model: Any = None  # Lazy-loaded
        self._feature_extractor = AudioFeatureExtractor()
        self._detector = AudioAIDetector()
        self._manipulation_detector = ManipulationDetector()
        self._trust_engine = TrustScoreEngine()
        self._ai_probability_engine = AIProbabilityEngine()
        self._gemini_service = GeminiService(settings)

    # ── Public API ─────────────────────────────────────────────────────────

    def analyze(self, audio_path: str) -> AudioAnalysisResponse:
        """
        Run the complete audio analysis pipeline.

        Args:
            audio_path: Absolute path to the temporary audio file.

        Returns:
            AudioAnalysisResponse with all fields populated.

        Raises:
            AudioServiceError: For unrecoverable pipeline failures.
        """
        # ── Phase 1: Speech-to-Text ─────────────────────────────────────
        logger.info("Phase 1: Speech-to-text transcription")
        whisper_result = self._transcribe(audio_path)
        transcript = whisper_result.transcript

        if not transcript.strip():
            logger.warning("Transcription produced empty transcript — using placeholder")
            transcript = "[No speech detected in audio]"

        # ── Phase 2: Audio Feature Extraction ──────────────────────────
        logger.info("Phase 2: Audio feature extraction")
        features = self._feature_extractor.extract(audio_path)

        # ── Phase 3: AI Audio Detection ────────────────────────────────
        logger.info("Phase 3: Heuristic AI audio detection")
        detection_result = self._detector.detect(features)

        # ── Phase 4: Gemini Explainability ─────────────────────────────
        logger.info("Phase 4: Gemini audio explainability")
        audio_explanation, all_indicators = self._generate_audio_explanation(
            audio_ai_probability=detection_result.audio_ai_probability,
            classification=detection_result.classification,
            confidence=detection_result.confidence,
            audio_indicators=detection_result.audio_indicators,
            features=features,
            transcript=transcript,
        )

        # ── Phase 5: Transcript Trust Analysis ─────────────────────────
        logger.info("Phase 5: Transcript trust analysis (reusing existing engines)")
        transcript_analysis = self._analyze_transcript(transcript)

        # ── Assemble Response ───────────────────────────────────────────
        return AudioAnalysisResponse(
            audio_ai_probability=detection_result.audio_ai_probability,
            classification=detection_result.classification,
            confidence=detection_result.confidence,
            audio_indicators=all_indicators,
            transcript=transcript,
            transcript_analysis=transcript_analysis,
            audio_explanation=audio_explanation,
        )

    # ── Phase 1: Whisper STT ───────────────────────────────────────────────

    def _transcribe(self, audio_path: str) -> WhisperResult:
        """
        Transcribe audio using faster-whisper.

        Loads the model lazily on first call and caches it for subsequent requests.
        """
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise AudioServiceError(
                "faster-whisper is required for speech-to-text. "
                "Install with: pip install faster-whisper",
                http_status=500,
            ) from exc

        if self._whisper_model is None:
            model_size = os.environ.get("WHISPER_MODEL", _DEFAULT_WHISPER_MODEL)
            logger.info("Loading Whisper model: %s", model_size)
            try:
                # Use CPU with int8 quantization for lightweight inference
                self._whisper_model = WhisperModel(
                    model_size,
                    device="cpu",
                    compute_type="int8",
                )
                logger.info("Whisper model '%s' loaded successfully", model_size)
            except Exception as exc:
                raise AudioServiceError(
                    f"Failed to load Whisper model '{model_size}': {exc}",
                    http_status=500,
                ) from exc

        try:
            segments, info = self._whisper_model.transcribe(
                audio_path,
                beam_size=5,
                language=None,  # Auto-detect language
                vad_filter=True,  # Skip non-speech
            )
            # Collect all segment texts
            transcript_parts = [seg.text for seg in segments]
            full_transcript = " ".join(transcript_parts).strip()

            logger.info(
                "Transcription complete: language=%s (prob=%.2f) duration=%.1fs",
                info.language,
                info.language_probability,
                info.duration,
            )

            return WhisperResult(
                transcript=full_transcript,
                language=info.language,
                language_probability=info.language_probability,
                duration_seconds=info.duration,
            )
        except Exception as exc:
            raise AudioServiceError(
                f"Speech-to-text transcription failed: {exc}",
                http_status=422,
            ) from exc

    # ── Phase 4: Gemini Audio Explainability ───────────────────────────────

    def _generate_audio_explanation(
        self,
        audio_ai_probability: int,
        classification: str,
        confidence: str,
        audio_indicators: list[str],
        features: Any,
        transcript: str,
    ) -> tuple[str, list[str]]:
        """
        Generate audio explanation using Gemini structured output.

        Falls back to a rule-based explanation if Gemini is unavailable.
        Returns (explanation_text, merged_indicators).
        """
        all_indicators = list(audio_indicators)

        if not self._gemini_service.is_available:
            logger.warning("Gemini not configured — using fallback audio explanation")
            return self._fallback_explanation(audio_ai_probability, classification, audio_indicators), all_indicators

        try:
            prompt = self._build_audio_explanation_prompt(
                audio_ai_probability=audio_ai_probability,
                classification=classification,
                confidence=confidence,
                audio_indicators=audio_indicators,
                features=features,
                transcript=transcript[:2000],  # Limit to 2000 chars
            )

            client = self._gemini_service._get_client()
            from google.genai import types

            response = client.models.generate_content(
                model=self._settings.gemini_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.25,
                    response_mime_type="application/json",
                    response_schema=AudioGeminiExplanation,
                ),
            )

            raw = response.text
            if not raw:
                raise GeminiServiceError("Empty Gemini response for audio explainability")

            import json
            payload = json.loads(raw)
            gemini_result = AudioGeminiExplanation.model_validate(payload)

            # Merge additional indicators from Gemini
            for ind in gemini_result.additional_indicators:
                if ind not in all_indicators:
                    all_indicators.append(ind)

            explanation = gemini_result.audio_explanation
            logger.info("Gemini audio explanation generated successfully")
            return explanation, all_indicators

        except (GeminiServiceError, Exception) as exc:
            logger.warning("Gemini audio explainability failed — using fallback: %s", exc)
            return self._fallback_explanation(audio_ai_probability, classification, audio_indicators), all_indicators

    @staticmethod
    def _build_audio_explanation_prompt(
        audio_ai_probability: int,
        classification: str,
        confidence: str,
        audio_indicators: list[str],
        features: Any,
        transcript: str,
    ) -> str:
        indicators_str = "\n".join(f"  - {ind}" for ind in audio_indicators) if audio_indicators else "  - None detected"

        return f"""You are Technoax Audio Authenticity Intelligence Engine — an explainable AI system.

Analyze the following audio classification result and produce a detailed explanation.

AUDIO ANALYSIS RESULTS (authoritative — do not contradict):
- AI Probability Score: {audio_ai_probability}/100
- Classification: {classification}
- Confidence: {confidence}

DETECTED ACOUSTIC INDICATORS:
{indicators_str}

AUDIO METRICS:
- Pitch Mean: {features.pitch_mean:.1f} Hz
- Pitch CV (variation): {features.pitch_cv:.3f}
- Energy CV (uniformity): {features.energy_cv:.3f}
- Voice Stability: {features.voice_stability:.3f}
- Pause Count: {features.pause_count}
- Silence Ratio: {features.silence_ratio:.3f}
- Speaking Rate: {features.speaking_rate:.2f} syl/sec
- Duration: {features.duration_seconds:.1f} seconds

TRANSCRIPT (first 2000 chars):
\"\"\"{transcript}\"\"\"

Return valid JSON with:
1. audio_explanation — 3-5 sentences explaining why the audio was classified as "{classification}".
   Reference specific acoustic metrics. Be professional and technical but accessible.
2. confidence_explanation — 1 sentence explaining the "{confidence}" confidence level.
3. additional_indicators — list of any additional acoustic indicators you observe beyond those already listed.

Style: Professional, technical, evidence-based. No generic AI chatbot language.
"""

    @staticmethod
    def _fallback_explanation(
        probability: int,
        classification: str,
        indicators: list[str],
    ) -> str:
        """Rule-based fallback explanation when Gemini is unavailable."""
        indicator_str = (
            "; ".join(indicators[:4]) if indicators else "no specific indicators"
        )

        if probability <= 30:
            return (
                f"The audio registers an AI probability of {probability}/100, classified as '{classification}'. "
                f"The acoustic analysis detected characteristics consistent with natural human speech, including "
                f"natural prosodic variation, organic pause patterns, and pitch fluctuations typical of human voice. "
                f"Observed signals: {indicator_str}."
            )
        if probability <= 69:
            return (
                f"The audio registers an AI probability of {probability}/100, classified as '{classification}'. "
                f"The acoustic analysis found mixed signals — some features align with synthetic speech while "
                f"others suggest natural human characteristics. This may indicate voice-cloning technology, "
                f"professional studio recording, or naturally very consistent speech patterns. "
                f"Observed signals: {indicator_str}."
            )
        return (
            f"The audio registers an AI probability of {probability}/100, classified as '{classification}'. "
            f"The acoustic analysis detected characteristics commonly associated with text-to-speech synthesis, "
            f"including {indicator_str}. These patterns reflect the highly uniform prosody and consistent energy "
            f"distribution typical of AI-generated speech systems."
        )

    # ── Phase 5: Transcript Trust Analysis ────────────────────────────────

    def _analyze_transcript(self, transcript: str) -> TranscriptAnalysis:
        """
        Run the existing Technoax text analysis pipeline on the transcript.

        Reuses ManipulationDetector, TrustScoreEngine, AIProbabilityEngine.
        Does NOT call Gemini here to avoid redundant API usage.
        """
        if not transcript.strip() or transcript == "[No speech detected in audio]":
            return TranscriptAnalysis(
                trust_score=50,
                risk_level="Medium",
                ai_generated_probability=0,
            )

        try:
            # Step 1: Manipulation detection
            detection = self._manipulation_detector.detect(transcript)

            # Step 2: Trust score (rule-based only for transcript sub-analysis)
            rule_score, _, _ = self._trust_engine.calculate(
                detection.detected_patterns,
                detection.spans,
            )

            # Step 3: Derive risk level
            _, trust_meter = self._trust_engine.derive_from_score(rule_score)
            risk_level_enum, _ = self._trust_engine.derive_from_score(rule_score)

            # Step 4: AI probability for transcript text
            ai_prob_result = self._ai_probability_engine.compute_rule_based_probability(transcript)

            logger.info(
                "Transcript analysis: trust=%d risk=%s ai_prob=%d",
                rule_score,
                risk_level_enum.value,
                ai_prob_result.probability,
            )

            return TranscriptAnalysis(
                trust_score=rule_score,
                risk_level=risk_level_enum.value,
                ai_generated_probability=ai_prob_result.probability,
            )

        except Exception as exc:
            logger.warning("Transcript analysis failed — using defaults: %s", exc)
            return TranscriptAnalysis(
                trust_score=50,
                risk_level="Medium",
                ai_generated_probability=0,
            )


# ── Module-level singleton factory ──────────────────────────────────────────

@lru_cache
def get_audio_service(settings: Settings) -> AudioService:
    """Return a cached AudioService instance (Whisper model is expensive to load)."""
    return AudioService(settings)
