"""Confidence scoring system for trust analysis reliability.

Measures how confident the system is in its own trust score by considering
signal density, signal agreement, text length, and category diversity.
A trust score of 50 from 20 matched signals is far more reliable than
50 from a single weak signal.
"""

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ConfidenceResult:
    """Analysis confidence assessment."""

    confidence_score: int        # 0–100
    confidence_label: str        # "Very High", "High", "Moderate", "Low"
    reasoning: str               # Human-readable explanation
    signal_density: float        # Matches per 100 words
    signal_agreement: float      # Rule-Gemini agreement factor (0.0–1.0)


class ConfidenceScorer:
    """
    Scores the system's confidence in its trust analysis.

    Factors:
    1. Signal Density — more detected signals → higher confidence
    2. Signal Agreement — rule-based and Gemini scores in alignment → higher confidence
    3. Text Length — very short texts get lower confidence
    4. Category Diversity — multiple manipulation categories → higher confidence
    """

    def compute(
        self,
        text: str,
        detected_pattern_count: int,
        matched_word_count: int,
        rule_score: int,
        gemini_score: int | None,
    ) -> ConfidenceResult:
        """
        Compute confidence in the trust analysis.

        Args:
            text: Original analyzed text.
            detected_pattern_count: Number of unique manipulation categories detected.
            matched_word_count: Total number of matched manipulation words.
            rule_score: Rule-based trust score (0–100).
            gemini_score: Gemini contextual trust score (0–100), or None if unavailable.

        Returns:
            ConfidenceResult with score, label, and reasoning.
        """
        word_count = len(text.split()) if text else 0

        # Factor 1: Signal Density (0–30 points)
        density_score, signal_density = self._signal_density_factor(
            matched_word_count, word_count
        )

        # Factor 2: Signal Agreement (0–30 points)
        agreement_score, agreement_factor = self._signal_agreement_factor(
            rule_score, gemini_score
        )

        # Factor 3: Text Length (0–20 points)
        length_score = self._text_length_factor(word_count)

        # Factor 4: Category Diversity (0–20 points)
        diversity_score = self._category_diversity_factor(detected_pattern_count)

        # Composite confidence
        raw_confidence = density_score + agreement_score + length_score + diversity_score
        confidence_score = max(0, min(100, raw_confidence))
        confidence_label = self._score_to_label(confidence_score)

        # Build reasoning
        factors = []
        if density_score >= 20:
            factors.append("strong signal density")
        elif density_score >= 10:
            factors.append("moderate signal density")
        else:
            factors.append("low signal density")

        if gemini_score is not None:
            if agreement_score >= 20:
                factors.append("high rule-Gemini agreement")
            elif agreement_score >= 10:
                factors.append("moderate rule-Gemini agreement")
            else:
                factors.append("low rule-Gemini agreement")
        else:
            factors.append("no Gemini cross-validation")

        if length_score >= 15:
            factors.append("sufficient text length")
        else:
            factors.append("limited text length")

        if diversity_score >= 15:
            factors.append("diverse signal categories")
        elif diversity_score >= 8:
            factors.append("moderate category diversity")

        reasoning = (
            f"Confidence {confidence_score}/100 ({confidence_label}): "
            + ", ".join(factors) + "."
        )

        return ConfidenceResult(
            confidence_score=confidence_score,
            confidence_label=confidence_label,
            reasoning=reasoning,
            signal_density=round(signal_density, 2),
            signal_agreement=round(agreement_factor, 2),
        )

    @staticmethod
    def _signal_density_factor(
        matched_count: int, word_count: int
    ) -> tuple[int, float]:
        """
        Score based on manipulation signal density.

        More signals per 100 words → higher confidence in the analysis.
        """
        if word_count == 0:
            return 5, 0.0

        density = (matched_count / word_count) * 100  # matches per 100 words

        if density > 5.0:
            return 30, density
        if density > 3.0:
            return 25, density
        if density > 1.5:
            return 18, density
        if density > 0.5:
            return 12, density
        if matched_count > 0:
            return 8, density
        return 5, density  # No matches → low but non-zero (clean text is also a signal)

    @staticmethod
    def _signal_agreement_factor(
        rule_score: int, gemini_score: int | None
    ) -> tuple[int, float]:
        """
        Score based on agreement between rule-based and Gemini analysis.

        When both engines agree, confidence is high.
        """
        if gemini_score is None:
            return 10, 0.0  # Partial confidence without cross-validation

        difference = abs(rule_score - gemini_score)
        agreement = 1.0 - (difference / 100.0)

        if difference <= 10:
            return 30, agreement  # Strong agreement
        if difference <= 20:
            return 22, agreement
        if difference <= 35:
            return 15, agreement
        if difference <= 50:
            return 8, agreement
        return 3, agreement  # Major disagreement

    @staticmethod
    def _text_length_factor(word_count: int) -> int:
        """
        Score based on text length — longer texts provide more signal.
        """
        if word_count >= 200:
            return 20
        if word_count >= 100:
            return 16
        if word_count >= 50:
            return 12
        if word_count >= 20:
            return 8
        return 4

    @staticmethod
    def _category_diversity_factor(pattern_count: int) -> int:
        """
        Score based on the number of unique manipulation categories detected.
        """
        if pattern_count >= 4:
            return 20
        if pattern_count >= 3:
            return 16
        if pattern_count >= 2:
            return 12
        if pattern_count >= 1:
            return 8
        return 5  # Clean text — still a meaningful result

    @staticmethod
    def _score_to_label(score: int) -> str:
        """Map confidence score to human-readable label."""
        if score >= 80:
            return "Very High"
        if score >= 60:
            return "High"
        if score >= 40:
            return "Moderate"
        return "Low"
