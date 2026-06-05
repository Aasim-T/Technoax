"""Statistical AI-generation probability engine with multi-signal detection.

Provides rule-based AI detection that works independently of Gemini,
plus hybrid blending when Gemini scores are available. Analyzes linguistic
patterns that distinguish human writing from LLM outputs.
"""

import math
import re
import logging
from collections import Counter
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Sub-signal weights for rule-based AI probability
# ---------------------------------------------------------------------------
SIGNAL_WEIGHTS = {
    "burstiness": 0.25,
    "vocabulary_richness": 0.20,
    "repetitive_structure": 0.20,
    "formality_index": 0.15,
    "perplexity_proxy": 0.20,
}

# Hybrid blending: 60% rule-based, 40% Gemini
RULE_WEIGHT = 0.60
GEMINI_WEIGHT = 0.40


@dataclass(frozen=True)
class SignalScore:
    """Individual sub-signal score with explainability."""

    name: str
    score: int          # 0–100 (higher = more likely AI)
    weight: float       # Contribution weight
    reasoning: str      # Human-readable explanation


@dataclass(frozen=True)
class AIProbabilityResult:
    """Full AI probability analysis with breakdown."""

    probability: int                   # 0–100 composite score
    label: str                         # Human-readable label
    signals: list[SignalScore]         # Per-signal breakdown
    reasoning: str                     # Overall explanation


class AIProbabilityEngine:
    """
    Multi-signal statistical engine for AI-generation detection.

    Sub-signals:
    1. Burstiness — sentence length variance (LLMs produce uniform lengths)
    2. Vocabulary Richness — Type-Token Ratio (LLMs tend toward lower diversity)
    3. Repetitive Structure — N-gram repetition analysis
    4. Formality Index — Overly polished / hedged language patterns
    5. Perplexity Proxy — Word predictability via character-level entropy
    """

    # ── Formality markers ──────────────────────────────────────────────
    _HEDGE_PHRASES = (
        "it is important to note", "it should be noted", "it is worth mentioning",
        "in conclusion", "furthermore", "moreover", "additionally", "consequently",
        "significantly", "particularly", "specifically", "fundamentally",
        "comprehensively", "systematically", "effectively", "efficiently",
        "ultimately", "essentially", "inherently", "notably",
        "in this context", "in light of", "with respect to", "in terms of",
        "it is essential", "it is crucial", "it is noteworthy", "it is evident",
        "this underscores", "this highlights", "this demonstrates", "this illustrates",
        "leveraging", "utilizing", "facilitating", "implementing",
        "a comprehensive", "a systematic", "a transformative", "a significant",
        "across multiple domains", "in various contexts", "from multiple perspectives",
    )

    _AI_SENTENCE_STARTERS = (
        "as an ai", "as a language model", "i cannot", "i don't have",
        "based on the information", "based on available", "according to",
        "in summary", "to summarize", "in essence",
    )

    def compute_rule_based_probability(self, text: str) -> AIProbabilityResult:
        """
        Analyze text with all sub-signals and produce a composite AI probability score.

        Returns a full breakdown for explainability.
        """
        if not text or len(text.strip()) < 20:
            return AIProbabilityResult(
                probability=0,
                label="Insufficient Text",
                signals=[],
                reasoning="Text is too short for meaningful AI-generation analysis.",
            )

        signals = [
            self._compute_burstiness(text),
            self._compute_vocabulary_richness(text),
            self._compute_repetitive_structure(text),
            self._compute_formality_index(text),
            self._compute_perplexity_proxy(text),
        ]

        # Weighted composite score
        composite = sum(s.score * s.weight for s in signals)
        probability = max(0, min(100, int(composite)))
        label = self._probability_to_label(probability)

        # Build overall reasoning
        top_signals = sorted(signals, key=lambda s: s.score, reverse=True)[:3]
        signal_descriptions = "; ".join(
            f"{s.name} ({s.score}/100)" for s in top_signals
        )
        reasoning = (
            f"Statistical analysis yields {probability}% AI-generation likelihood. "
            f"Strongest indicators: {signal_descriptions}."
        )

        return AIProbabilityResult(
            probability=probability,
            label=label,
            signals=signals,
            reasoning=reasoning,
        )

    @staticmethod
    def compute_hybrid_probability(
        rule_score: int,
        gemini_score: int,
    ) -> int:
        """
        Blend rule-based and Gemini AI probability scores.

        60% statistical (rule), 40% Gemini contextual.
        """
        hybrid = int(rule_score * RULE_WEIGHT + gemini_score * GEMINI_WEIGHT)
        return max(0, min(100, hybrid))

    # ── Sub-signal implementations ─────────────────────────────────────

    def _compute_burstiness(self, text: str) -> SignalScore:
        """
        Measure sentence length variance (burstiness).

        Human writing has high variance (short + long sentences).
        LLMs tend toward uniform sentence lengths → low burstiness → high AI score.
        """
        sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]

        if len(sentences) < 3:
            return SignalScore(
                name="Burstiness",
                score=30,
                weight=SIGNAL_WEIGHTS["burstiness"],
                reasoning="Too few sentences for reliable burstiness measurement.",
            )

        lengths = [len(s.split()) for s in sentences]
        mean_length = sum(lengths) / len(lengths)

        if mean_length == 0:
            return SignalScore(
                name="Burstiness",
                score=50,
                weight=SIGNAL_WEIGHTS["burstiness"],
                reasoning="Sentences have no measurable word content.",
            )

        # Coefficient of variation (CV) — lower = more uniform = more AI-like
        variance = sum((l - mean_length) ** 2 for l in lengths) / len(lengths)
        std_dev = math.sqrt(variance)
        cv = std_dev / mean_length

        # Map CV to AI score: CV < 0.2 → high AI, CV > 0.6 → low AI
        if cv < 0.15:
            score = 90
            reasoning = "Very uniform sentence lengths — strong AI pattern."
        elif cv < 0.25:
            score = 70
            reasoning = "Low sentence length variance — moderate AI indicator."
        elif cv < 0.40:
            score = 45
            reasoning = "Moderate sentence length variance — inconclusive."
        elif cv < 0.60:
            score = 25
            reasoning = "Good sentence length variance — likely human writing."
        else:
            score = 10
            reasoning = "High burstiness — characteristic of human writing."

        return SignalScore(
            name="Burstiness",
            score=score,
            weight=SIGNAL_WEIGHTS["burstiness"],
            reasoning=reasoning,
        )

    def _compute_vocabulary_richness(self, text: str) -> SignalScore:
        """
        Type-Token Ratio (TTR) analysis.

        LLMs tend to use a narrower vocabulary proportionally, especially in
        medium-length texts. Very high TTR in short texts is normal.
        """
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())

        if len(words) < 10:
            return SignalScore(
                name="Vocabulary Richness",
                score=30,
                weight=SIGNAL_WEIGHTS["vocabulary_richness"],
                reasoning="Too few words for reliable vocabulary analysis.",
            )

        # Use root TTR (Guiraud's index) to normalize for text length
        unique_words = len(set(words))
        total_words = len(words)
        guiraud = unique_words / math.sqrt(total_words)

        # Typical ranges: human writing 6–10+, LLM text 4–7
        if guiraud < 4.0:
            score = 80
            reasoning = "Low vocabulary richness — strong AI pattern."
        elif guiraud < 5.5:
            score = 60
            reasoning = "Below-average vocabulary diversity — moderate AI indicator."
        elif guiraud < 7.0:
            score = 35
            reasoning = "Average vocabulary richness — inconclusive."
        elif guiraud < 9.0:
            score = 20
            reasoning = "Above-average vocabulary diversity — likely human."
        else:
            score = 10
            reasoning = "Very rich vocabulary — strongly suggests human writing."

        return SignalScore(
            name="Vocabulary Richness",
            score=score,
            weight=SIGNAL_WEIGHTS["vocabulary_richness"],
            reasoning=reasoning,
        )

    def _compute_repetitive_structure(self, text: str) -> SignalScore:
        """
        N-gram repetition analysis.

        LLMs often repeat structural patterns (e.g., "This is a...",
        "It is important to..."). Measures trigram repetition rate.
        """
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())

        if len(words) < 15:
            return SignalScore(
                name="Repetitive Structure",
                score=30,
                weight=SIGNAL_WEIGHTS["repetitive_structure"],
                reasoning="Too few words for n-gram repetition analysis.",
            )

        # Build trigrams
        trigrams = [tuple(words[i:i + 3]) for i in range(len(words) - 2)]
        trigram_counts = Counter(trigrams)

        total_trigrams = len(trigrams)
        repeated_trigrams = sum(1 for count in trigram_counts.values() if count > 1)
        repetition_rate = repeated_trigrams / len(trigram_counts) if trigram_counts else 0

        if repetition_rate > 0.30:
            score = 85
            reasoning = "Very high trigram repetition — strong AI structural pattern."
        elif repetition_rate > 0.20:
            score = 65
            reasoning = "Elevated structural repetition — moderate AI indicator."
        elif repetition_rate > 0.10:
            score = 40
            reasoning = "Some structural repetition — inconclusive."
        else:
            score = 15
            reasoning = "Low structural repetition — likely human variation."

        return SignalScore(
            name="Repetitive Structure",
            score=score,
            weight=SIGNAL_WEIGHTS["repetitive_structure"],
            reasoning=reasoning,
        )

    def _compute_formality_index(self, text: str) -> SignalScore:
        """
        Detect overly formal, hedged, or polished language patterns.

        LLMs tend to produce text with excessive hedging, formal transitions,
        and qualification phrases that human writers rarely use at such density.
        """
        text_lower = text.lower()
        word_count = len(text.split())

        if word_count < 10:
            return SignalScore(
                name="Formality Index",
                score=30,
                weight=SIGNAL_WEIGHTS["formality_index"],
                reasoning="Too short for formality analysis.",
            )

        # Count hedge phrases
        hedge_count = sum(1 for phrase in self._HEDGE_PHRASES if phrase in text_lower)

        # Count AI self-references
        ai_starter_count = sum(1 for s in self._AI_SENTENCE_STARTERS if s in text_lower)

        # Normalize by text length (per 100 words)
        hedge_density = (hedge_count / word_count) * 100
        ai_density = (ai_starter_count / word_count) * 100

        # Direct AI self-reference is very strong signal
        if ai_density > 0:
            score = min(95, 70 + int(ai_density * 50))
            reasoning = "Contains AI self-referencing language — very strong AI indicator."
        elif hedge_density > 3.0:
            score = 85
            reasoning = "Extremely high hedge phrase density — strong AI formality pattern."
        elif hedge_density > 1.5:
            score = 65
            reasoning = "Elevated formal hedging — moderate AI indicator."
        elif hedge_density > 0.5:
            score = 40
            reasoning = "Some formal language — inconclusive."
        else:
            score = 15
            reasoning = "Natural, informal tone — suggests human writing."

        return SignalScore(
            name="Formality Index",
            score=score,
            weight=SIGNAL_WEIGHTS["formality_index"],
            reasoning=reasoning,
        )

    def _compute_perplexity_proxy(self, text: str) -> SignalScore:
        """
        Character-level entropy as a proxy for perplexity.

        LLM text tends to have lower entropy (more predictable character
        distributions) compared to human writing with typos, colloquialisms,
        and varied punctuation.
        """
        if len(text) < 20:
            return SignalScore(
                name="Perplexity Proxy",
                score=30,
                weight=SIGNAL_WEIGHTS["perplexity_proxy"],
                reasoning="Too short for entropy analysis.",
            )

        # Character-level entropy (Shannon entropy)
        text_clean = text.lower()
        char_counts = Counter(text_clean)
        total_chars = len(text_clean)

        entropy = -sum(
            (count / total_chars) * math.log2(count / total_chars)
            for count in char_counts.values()
            if count > 0
        )

        # Typical ranges: LLM text 3.5–4.2, human text 4.0–5.0+
        if entropy < 3.5:
            score = 75
            reasoning = "Low character entropy — predictable text pattern."
        elif entropy < 4.0:
            score = 55
            reasoning = "Below-average entropy — moderate predictability."
        elif entropy < 4.5:
            score = 35
            reasoning = "Average entropy — inconclusive."
        else:
            score = 15
            reasoning = "High entropy — suggests human-written variability."

        return SignalScore(
            name="Perplexity Proxy",
            score=score,
            weight=SIGNAL_WEIGHTS["perplexity_proxy"],
            reasoning=reasoning,
        )

    @staticmethod
    def _probability_to_label(probability: int) -> str:
        """Map AI probability score to human-readable label."""
        if probability >= 81:
            return "Highly Likely AI-Generated"
        if probability >= 51:
            return "Strong AI Indicators"
        if probability >= 21:
            return "Possibly AI-Assisted"
        return "Likely Human-Written"
