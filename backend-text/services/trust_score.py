"""Trust score, risk level, and trust meter computation."""

from models.response_models import RiskLevel, TrustMeter
from services.pattern_catalog import (
    BASE_TRUST_SCORE,
    CONSPIRACY_URGENCY_COMBO_PENALTY,
    MULTI_CATEGORY_PENALTY,
    PENALTY_BY_SEVERITY,
    REPEAT_MATCH_PENALTY,
    ManipulationCategory,
    Severity,
)
from services.text_match_utils import TextSpanMatch

RULE_SCORE_WEIGHT = 0.7
GEMINI_SCORE_WEIGHT = 0.3


class TrustScoreEngine:
    """Computes trust score, risk level, and trust meter from detected manipulation signals."""

    def calculate(
        self,
        detected_patterns: list[str],
        spans: list[TextSpanMatch] | None = None,
    ) -> tuple[int, RiskLevel, TrustMeter]:
        """
        Compute rule-based trust score with severity-weighted and multi-match penalties.

        Args:
            detected_patterns: Unique manipulation categories detected.
            spans: Word-level matches with per-phrase severity (preferred).
        """
        if spans:
            score = self._score_from_spans(detected_patterns, spans)
        else:
            score = self._score_from_categories_only(detected_patterns)

        score = max(0, min(100, score))
        return score, self._score_to_risk_level(score), self._score_to_trust_meter(score)

    @staticmethod
    def _score_from_spans(detected_patterns: list[str], spans: list[TextSpanMatch]) -> int:
        """Apply per-match severity penalties plus multi-match adjustments."""
        score = BASE_TRUST_SCORE

        for span in spans:
            try:
                severity = Severity(span.severity)
            except ValueError:
                severity = Severity.MEDIUM
            score -= PENALTY_BY_SEVERITY.get(severity, PENALTY_BY_SEVERITY[Severity.MEDIUM])

        if len(detected_patterns) >= 2:
            score -= MULTI_CATEGORY_PENALTY * (len(detected_patterns) - 1)

        repeat_penalty = max(0, len(spans) - len(detected_patterns)) * REPEAT_MATCH_PENALTY
        score -= repeat_penalty

        categories = set(detected_patterns)
        if (
            ManipulationCategory.CONSPIRACY.value in categories
            and ManipulationCategory.URGENCY.value in categories
        ):
            score -= CONSPIRACY_URGENCY_COMBO_PENALTY

        return score

    @staticmethod
    def _score_from_categories_only(detected_patterns: list[str]) -> int:
        """Fallback when span data is unavailable."""
        score = BASE_TRUST_SCORE
        for _ in detected_patterns:
            score -= PENALTY_BY_SEVERITY[Severity.MEDIUM]
        return score

    @staticmethod
    def compute_hybrid_score(rule_score: int, gemini_score: int) -> int:
        """
        Blend rule-based and Gemini contextual scores (70% rule / 30% Gemini).

        Rule engine remains the primary trust authority.
        """
        hybrid = int(
            (rule_score * RULE_SCORE_WEIGHT) + (gemini_score * GEMINI_SCORE_WEIGHT)
        )
        return max(0, min(100, hybrid))

    def derive_from_score(self, score: int) -> tuple[RiskLevel, TrustMeter]:
        """Map a final hybrid trust score to risk level and trust meter."""
        clamped = max(0, min(100, score))
        return self._score_to_risk_level(clamped), self._score_to_trust_meter(clamped)

    @staticmethod
    def _score_to_risk_level(score: int) -> RiskLevel:
        """Map numeric trust score to Low / Medium / High risk."""
        if score >= 80:
            return RiskLevel.LOW
        if score >= 50:
            return RiskLevel.MEDIUM
        return RiskLevel.HIGH

    @staticmethod
    def _score_to_trust_meter(score: int) -> TrustMeter:
        """Map numeric trust score to human-readable trust meter label."""
        if score >= 80:
            return TrustMeter.HIGH_TRUST
        if score >= 50:
            return TrustMeter.MODERATE_TRUST
        return TrustMeter.LOW_TRUST
