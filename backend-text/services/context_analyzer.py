"""Contextual domain classification with severity-weighted trust adjustments.

Classifies text into domain contexts (Medical, Financial, Political, General)
and applies context-aware severity multipliers. Medical misinformation is
weighted more heavily than entertainment clickbait.
"""

import re
import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class DomainType(str, Enum):
    """Content domain classification."""

    MEDICAL = "Medical"
    FINANCIAL = "Financial"
    POLITICAL = "Political"
    GENERAL = "General"


# Severity multipliers by domain — applied to base manipulation penalties
DOMAIN_SEVERITY_MULTIPLIERS: dict[DomainType, float] = {
    DomainType.MEDICAL: 1.5,    # Health misinformation is life-threatening
    DomainType.FINANCIAL: 1.3,  # Financial manipulation causes material harm
    DomainType.POLITICAL: 1.2,  # Political manipulation undermines democracy
    DomainType.GENERAL: 1.0,    # Baseline
}


@dataclass(frozen=True)
class DomainContext:
    """Domain classification result with confidence and reasoning."""

    domain: DomainType
    confidence: float           # 0.0 – 1.0
    severity_multiplier: float
    reasoning: str
    matched_indicators: list[str]


class ContextAnalyzer:
    """
    Classifies text content into domain contexts for severity-weighted trust analysis.

    Uses keyword-density heuristics per domain. The domain with the highest
    normalized hit rate wins, provided it exceeds a confidence threshold.
    """

    # ── Domain keyword dictionaries ─────────────────────────────────────

    _MEDICAL_KEYWORDS = {
        # High-signal medical terms
        "diagnosis", "treatment", "vaccine", "pharmaceutical", "medication",
        "prescription", "clinical trial", "side effects", "symptoms", "chronic",
        "cancer", "tumor", "disease", "infection", "therapy", "dosage",
        "antibiotic", "immune system", "blood pressure", "cholesterol",
        "diabetes", "surgery", "hospital", "patient", "health condition",
        "medical advice", "doctor", "physician", "nurse", "healthcare",
        "remedy", "cure", "wellness", "supplement", "detox", "herbal",
        "holistic", "homeopathic", "antiviral", "pandemic", "epidemic",
    }

    _FINANCIAL_KEYWORDS = {
        "investment", "stock market", "cryptocurrency", "bitcoin", "trading",
        "portfolio", "guaranteed returns", "passive income", "forex", "dividend",
        "mutual fund", "hedge fund", "interest rate", "inflation", "recession",
        "financial freedom", "millionaire", "wealth", "profit", "revenue",
        "tax", "bank account", "credit score", "debt", "mortgage", "loan",
        "insurance", "retirement", "pension", "compound interest",
        "get rich", "make money", "earn money", "side hustle", "cash flow",
    }

    _POLITICAL_KEYWORDS = {
        "election", "government", "politician", "democrat", "republican",
        "liberal", "conservative", "legislation", "policy", "congress",
        "parliament", "president", "prime minister", "voter", "ballot",
        "campaign", "political party", "left wing", "right wing", "propaganda",
        "immigration", "border", "tax reform", "regulation", "lobbying",
        "corruption", "constitutional", "amendment", "executive order",
        "socialism", "capitalism", "authoritarian", "democracy", "regime",
    }

    def classify_domain(self, text: str) -> DomainContext:
        """
        Classify the primary domain of the text content.

        Uses normalized keyword density to determine the most likely domain.
        """
        if not text or len(text.strip()) < 10:
            return DomainContext(
                domain=DomainType.GENERAL,
                confidence=1.0,
                severity_multiplier=1.0,
                reasoning="Text too short for domain classification.",
                matched_indicators=[],
            )

        text_lower = text.lower()

        # Count keyword matches per domain
        medical_matches = self._find_keyword_matches(text_lower, self._MEDICAL_KEYWORDS)
        financial_matches = self._find_keyword_matches(text_lower, self._FINANCIAL_KEYWORDS)
        political_matches = self._find_keyword_matches(text_lower, self._POLITICAL_KEYWORDS)

        # Build scores
        scores = {
            DomainType.MEDICAL: len(medical_matches),
            DomainType.FINANCIAL: len(financial_matches),
            DomainType.POLITICAL: len(political_matches),
        }

        matches_map = {
            DomainType.MEDICAL: medical_matches,
            DomainType.FINANCIAL: financial_matches,
            DomainType.POLITICAL: political_matches,
        }

        # Find the winning domain
        best_domain = max(scores, key=scores.get)  # type: ignore[arg-type]
        best_count = scores[best_domain]

        # Minimum threshold: at least 2 domain-specific keywords
        if best_count < 2:
            return DomainContext(
                domain=DomainType.GENERAL,
                confidence=0.8,
                severity_multiplier=DOMAIN_SEVERITY_MULTIPLIERS[DomainType.GENERAL],
                reasoning="No strong domain-specific signals detected; classified as general content.",
                matched_indicators=[],
            )

        # Confidence based on keyword density and margin over second-best
        total_matches = sum(scores.values())
        confidence = min(1.0, best_count / max(total_matches, 1))

        # Boost confidence if margin is clear
        sorted_scores = sorted(scores.values(), reverse=True)
        if len(sorted_scores) > 1 and sorted_scores[0] > sorted_scores[1] * 2:
            confidence = min(1.0, confidence + 0.15)

        multiplier = DOMAIN_SEVERITY_MULTIPLIERS[best_domain]
        matched = matches_map[best_domain][:10]  # Top 10 indicators

        reasoning = (
            f"Classified as {best_domain.value} content with {best_count} domain-specific "
            f"indicators. Severity multiplier: {multiplier}x."
        )

        return DomainContext(
            domain=best_domain,
            confidence=round(confidence, 2),
            severity_multiplier=multiplier,
            reasoning=reasoning,
            matched_indicators=matched,
        )

    def adjust_severity_weight(self, base_penalty: int, domain: DomainType) -> int:
        """
        Apply domain-specific severity multiplier to a base manipulation penalty.

        Medical misinformation penalties are 50% heavier than general content.
        """
        multiplier = DOMAIN_SEVERITY_MULTIPLIERS.get(domain, 1.0)
        return int(base_penalty * multiplier)

    @staticmethod
    def _find_keyword_matches(text_lower: str, keywords: set[str]) -> list[str]:
        """Find all keywords present in the text (case-insensitive)."""
        matches = []
        for keyword in sorted(keywords, key=len, reverse=True):
            pattern = re.compile(r'\b' + re.escape(keyword) + r'\b', re.IGNORECASE)
            if pattern.search(text_lower):
                matches.append(keyword)
        return matches
