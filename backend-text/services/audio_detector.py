"""Heuristic AI audio detection engine.

Takes extracted AudioFeatures and produces an AI probability score (0-100)
with a human-readable classification and list of detected audio indicators.

Scoring logic
-------------
Six heuristic signals are evaluated, each scored 0-100 (higher = more AI-like):

  1. Pitch Stability     – Low pitch variance → AI TTS
  2. Energy Uniformity   – Low energy CV → consistent robot-like output
  3. Voice Stability     – High stability index → monotone
  4. Pause Naturalness   – Absence of natural pauses → AI-like
  5. Speaking Rate       – Perfectly uniform rate → AI-like
  6. Spectral Regularity – Low spectral centroid std → synthesized tone

Weighted composite → audio_ai_probability (0-100)

This module is self-contained and has NO dependency on any existing
Technoax service module.
"""

import logging
from dataclasses import dataclass

from services.audio_features import AudioFeatures

logger = logging.getLogger(__name__)


# ── Signal weights ──────────────────────────────────────────────────────────
_WEIGHTS = {
    "pitch_stability":     0.30,
    "energy_uniformity":   0.20,
    "voice_stability":     0.20,
    "pause_naturalness":   0.15,
    "speaking_rate":       0.10,
    "spectral_regularity": 0.05,
}

# Probability → classification thresholds
_HUMAN_MAX = 30
_UNCERTAIN_MAX = 69


@dataclass(frozen=True)
class AudioDetectionResult:
    """Output of the AI audio detection engine."""

    audio_ai_probability: int       # 0-100
    classification: str             # "Likely Human" / "Uncertain" / "Likely AI Generated"
    confidence: str                 # "Low" / "Medium" / "High"
    audio_indicators: list[str]     # Observed acoustic indicators


class AudioAIDetector:
    """
    Heuristic AI audio detection engine.

    Analyzes extracted audio features to estimate whether speech was
    produced by a human or a text-to-speech / AI voice system.
    """

    def detect(self, features: AudioFeatures) -> AudioDetectionResult:
        """
        Run heuristic scoring on extracted audio features.

        Args:
            features: AudioFeatures dataclass from AudioFeatureExtractor.

        Returns:
            AudioDetectionResult with probability, classification, and indicators.
        """
        scores: dict[str, int] = {}
        indicators: list[str] = []

        # 1. Pitch Stability
        ps, pi = self._score_pitch_stability(features)
        scores["pitch_stability"] = ps
        indicators.extend(pi)

        # 2. Energy Uniformity
        eu, ei = self._score_energy_uniformity(features)
        scores["energy_uniformity"] = eu
        indicators.extend(ei)

        # 3. Voice Stability
        vs, vi = self._score_voice_stability(features)
        scores["voice_stability"] = vs
        indicators.extend(vi)

        # 4. Pause Naturalness
        pn, pni = self._score_pause_naturalness(features)
        scores["pause_naturalness"] = pn
        indicators.extend(pni)

        # 5. Speaking Rate
        sr, sri = self._score_speaking_rate(features)
        scores["speaking_rate"] = sr
        indicators.extend(sri)

        # 6. Spectral Regularity
        spec, speci = self._score_spectral_regularity(features)
        scores["spectral_regularity"] = spec
        indicators.extend(speci)

        # Weighted composite
        composite = sum(
            scores[signal] * weight for signal, weight in _WEIGHTS.items()
        )
        probability = max(0, min(100, int(round(composite))))

        classification = self._classify(probability)
        confidence = self._confidence(probability, features)

        logger.info(
            "Audio AI detection: probability=%d classification='%s' confidence='%s' "
            "signal_scores=%s",
            probability,
            classification,
            confidence,
            scores,
        )

        return AudioDetectionResult(
            audio_ai_probability=probability,
            classification=classification,
            confidence=confidence,
            audio_indicators=list(dict.fromkeys(indicators)),  # dedupe, preserve order
        )

    # ── Signal scorers ──────────────────────────────────────────────────────

    @staticmethod
    def _score_pitch_stability(features: AudioFeatures) -> tuple[int, list[str]]:
        """
        Low pitch variance → AI TTS.
        Measured via pitch coefficient of variation (CV = std / mean).
        """
        indicators: list[str] = []
        cv = features.pitch_cv

        if features.pitch_mean == 0.0:
            # No voiced frames detected — treat as neutral
            return 50, ["Insufficient voiced audio for pitch analysis"]

        if cv < 0.05:
            score = 90
            indicators.append("Extremely stable pitch (robotic monotone)")
        elif cv < 0.10:
            score = 75
            indicators.append("Low pitch variation")
        elif cv < 0.18:
            score = 50
            indicators.append("Moderate pitch variation")
        elif cv < 0.30:
            score = 25
            indicators.append("Natural pitch fluctuations")
        else:
            score = 10
            indicators.append("High pitch expressiveness (human prosody)")

        return score, indicators

    @staticmethod
    def _score_energy_uniformity(features: AudioFeatures) -> tuple[int, list[str]]:
        """
        Low energy variance → consistent synthetic output.
        """
        indicators: list[str] = []
        cv = features.energy_cv

        if features.energy_mean == 0.0:
            return 50, []

        if cv < 0.15:
            score = 85
            indicators.append("Consistent energy distribution (no natural loudness variation)")
        elif cv < 0.25:
            score = 65
            indicators.append("Low energy variance")
        elif cv < 0.40:
            score = 40
            indicators.append("Moderate energy variation")
        else:
            score = 15
            indicators.append("Natural energy variation (expressive speech)")

        return score, indicators

    @staticmethod
    def _score_voice_stability(features: AudioFeatures) -> tuple[int, list[str]]:
        """
        Voice stability index: 1 - pitch_cv (clamped).
        High stability → AI-like monotone.
        """
        indicators: list[str] = []
        stability = features.voice_stability

        if stability > 0.92:
            score = 90
            indicators.append("Synthetic prosody (robotic voice stability)")
        elif stability > 0.82:
            score = 72
            indicators.append("High voice stability (minimal prosodic variation)")
        elif stability > 0.70:
            score = 45
            indicators.append("Moderate voice stability")
        elif stability > 0.55:
            score = 22
            indicators.append("Natural prosodic variation")
        else:
            score = 8
            indicators.append("Highly expressive voice (strong human prosody)")

        return score, indicators

    @staticmethod
    def _score_pause_naturalness(features: AudioFeatures) -> tuple[int, list[str]]:
        """
        AI TTS tends to have very few or no natural breathing pauses.
        """
        indicators: list[str] = []
        duration = features.duration_seconds

        if duration < 2.0:
            # Too short to measure pause patterns
            return 50, []

        # Expected ~1 pause per 8 seconds of speech for natural human speech
        expected_pauses = max(1, duration / 8.0)
        pause_ratio = features.pause_count / expected_pauses

        if pause_ratio < 0.2:
            score = 85
            indicators.append("Minimal breathing artifacts (no natural pauses)")
        elif pause_ratio < 0.5:
            score = 65
            indicators.append("Reduced pause frequency")
        elif pause_ratio < 1.0:
            score = 40
            indicators.append("Some natural pauses present")
        else:
            score = 15
            indicators.append("Natural pause and breathing patterns")

        return score, indicators

    @staticmethod
    def _score_speaking_rate(features: AudioFeatures) -> tuple[int, list[str]]:
        """
        AI TTS tends to maintain highly uniform speaking rate.
        Human speech rate: ~2-5 syllables/second with natural variation.
        """
        indicators: list[str] = []
        rate = features.speaking_rate

        if rate == 0.0:
            return 50, []

        # Very fast and very steady is AI-like
        if 2.8 <= rate <= 3.8:
            score = 70
            indicators.append("Uniform pacing (metronomic speaking rate)")
        elif 2.0 <= rate <= 5.0:
            score = 40
            indicators.append("Normal speaking rate")
        else:
            score = 20
            indicators.append("Irregular speaking rate (human-like variation)")

        return score, indicators

    @staticmethod
    def _score_spectral_regularity(features: AudioFeatures) -> tuple[int, list[str]]:
        """
        TTS systems often produce more spectrally uniform signals.
        Using spectral centroid as a proxy.
        """
        indicators: list[str] = []
        centroid = features.spectral_centroid_mean

        # TTS typically produces centroids in 1500-3000 Hz range
        if 1500 <= centroid <= 3000:
            score = 65
            indicators.append("Spectral profile consistent with TTS synthesis")
        elif 800 <= centroid <= 1500:
            score = 35
            indicators.append("Natural lower spectral range")
        else:
            score = 20
            indicators.append("Spectral profile suggests natural variation")

        return score, indicators

    # ── Classification helpers ──────────────────────────────────────────────

    @staticmethod
    def _classify(probability: int) -> str:
        if probability <= _HUMAN_MAX:
            return "Likely Human"
        if probability <= _UNCERTAIN_MAX:
            return "Uncertain"
        return "Likely AI Generated"

    @staticmethod
    def _confidence(probability: int, features: AudioFeatures) -> str:
        """
        Confidence is lower when:
        - The audio is very short (<5 seconds)
        - The score is near a classification boundary
        """
        boundary_distance = min(
            abs(probability - _HUMAN_MAX),
            abs(probability - (_UNCERTAIN_MAX + 1)),
        )

        low_data = features.duration_seconds < 5.0 or features.pitch_mean == 0.0

        if low_data or boundary_distance < 8:
            return "Low"
        if boundary_distance < 20:
            return "Medium"
        return "High"
