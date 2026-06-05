"""Enhanced 4-tier risk classification with contextual threat assessment.

Extends the existing 3-tier (Low/Medium/High) risk model with a Critical
tier and considers domain context, manipulation density, signal severity,
and social engineering indicators for nuanced risk classification.
"""

import logging
from dataclasses import dataclass
from enum import Enum

from services.context_analyzer import DomainType

logger = logging.getLogger(__name__)


class EnhancedRiskLevel(str, Enum):
    """Four-tier risk classification."""

    LOW = "Low Risk"
    MEDIUM = "Medium Risk"
    HIGH = "High Risk"
    CRITICAL = "Critical Risk"


@dataclass(frozen=True)
class EnhancedRiskResult:
    """Detailed risk classification with threat indicators."""

    level: EnhancedRiskLevel
    description: str
    threat_indicators: list[str]
    manipulation_density: float      # Manipulative signals per 100 words
    domain_risk_multiplier: float    # Applied domain severity multiplier
    is_critical: bool                # Whether content reached critical threshold


class EnhancedRiskClassifier:
    """
    Four-tier risk classifier that considers manipulation density,
    signal severity, domain context, and social engineering indicators.

    Risk tiers:
    - Low: trust_score >= 80, minimal manipulation signals
    - Medium: trust_score 50–79, some manipulation detected
    - High: trust_score 20–49, significant manipulation detected
    - Critical: trust_score < 20, OR high-danger domain + multiple severe signals
    """

    # Critical-risk criteria thresholds
    CRITICAL_SCORE_THRESHOLD = 20
    CRITICAL_MIN_CATEGORIES = 3
    HIGH_RISK_DOMAINS = {DomainType.MEDICAL, DomainType.FINANCIAL}

    def classify(
        self,
        trust_score: int,
        detected_patterns: list[str],
        social_engineering_categories: list[str],
        domain: DomainType,
        matched_word_count: int,
        text_word_count: int,
    ) -> EnhancedRiskResult:
        """
        Classify content risk with 4-tier granularity.

        Args:
            trust_score: Final hybrid trust score (0–100).
            detected_patterns: Manipulation categories from primary detector.
            social_engineering_categories: Categories from social engineering detector.
            domain: Classified domain context.
            matched_word_count: Total matched manipulation words.
            text_word_count: Total word count of analyzed text.
        """
        # Calculate manipulation density
        density = (
            (matched_word_count / text_word_count) * 100
            if text_word_count > 0
            else 0.0
        )

        # Total unique signal categories
        all_categories = list(set(detected_patterns + social_engineering_categories))
        category_count = len(all_categories)

        # Domain risk multiplier
        from services.context_analyzer import DOMAIN_SEVERITY_MULTIPLIERS
        domain_multiplier = DOMAIN_SEVERITY_MULTIPLIERS.get(domain, 1.0)

        # Build threat indicators
        threats = self._build_threat_indicators(
            detected_patterns,
            social_engineering_categories,
            domain,
            density,
        )

        # Determine risk level
        is_critical = self._is_critical(
            trust_score, category_count, domain, density
        )

        if is_critical:
            level = EnhancedRiskLevel.CRITICAL
            description = self._critical_description(domain, all_categories)
        elif trust_score < 40:
            level = EnhancedRiskLevel.HIGH
            description = (
                f"High risk content detected with {category_count} manipulation "
                f"categories and trust score {trust_score}/100."
            )
        elif trust_score < 70:
            level = EnhancedRiskLevel.MEDIUM
            description = (
                f"Moderate risk: {category_count} manipulation signal(s) detected "
                f"with trust score {trust_score}/100. Exercise caution."
            )
        else:
            level = EnhancedRiskLevel.LOW
            description = (
                f"Low risk content with trust score {trust_score}/100. "
                "Minimal manipulation indicators detected."
            )

        return EnhancedRiskResult(
            level=level,
            description=description,
            threat_indicators=threats,
            manipulation_density=round(density, 2),
            domain_risk_multiplier=domain_multiplier,
            is_critical=is_critical,
        )

    def _is_critical(
        self,
        trust_score: int,
        category_count: int,
        domain: DomainType,
        density: float,
    ) -> bool:
        """
        Determine if content reaches CRITICAL risk threshold.

        Critical conditions (any one triggers):
        1. Trust score below critical threshold (< 20)
        2. High-danger domain (Medical/Financial) + 3+ manipulation categories
        3. Extreme manipulation density (> 8% of words are manipulation signals)
        """
        if trust_score < self.CRITICAL_SCORE_THRESHOLD:
            return True

        if (
            domain in self.HIGH_RISK_DOMAINS
            and category_count >= self.CRITICAL_MIN_CATEGORIES
        ):
            return True

        if density > 8.0:
            return True

        return False

    def _critical_description(
        self, domain: DomainType, categories: list[str]
    ) -> str:
        """Generate a contextual description for critical-risk content."""
        domain_warning = ""
        if domain == DomainType.MEDICAL:
            domain_warning = (
                " Medical misinformation poses direct risk to health and safety."
            )
        elif domain == DomainType.FINANCIAL:
            domain_warning = (
                " Financial manipulation may result in significant material harm."
            )

        category_str = ", ".join(categories[:5])
        return (
            f"CRITICAL RISK: Content exhibits severe manipulation across "
            f"multiple dimensions ({category_str}).{domain_warning} "
            f"Independent verification is essential before any action."
        )

    @staticmethod
    def _build_threat_indicators(
        detected_patterns: list[str],
        se_categories: list[str],
        domain: DomainType,
        density: float,
    ) -> list[str]:
        """Build human-readable threat indicator list."""
        indicators: list[str] = []

        if "Fear" in detected_patterns:
            indicators.append("Fear-based emotional manipulation detected")
        if "Urgency" in detected_patterns:
            indicators.append("Artificial urgency/pressure tactics present")
        if "Clickbait" in detected_patterns:
            indicators.append("Sensationalized or misleading hooks identified")
        if "Conspiracy" in detected_patterns:
            indicators.append("Conspiracy framing or anti-establishment rhetoric")
        if "Emotional Trigger" in detected_patterns:
            indicators.append("Emotional exploitation targeting family/safety concerns")

        if "Authority Impersonation" in se_categories:
            indicators.append("False authority claims or credential abuse")
        if "Social Proof Abuse" in se_categories:
            indicators.append("Bandwagon/social proof manipulation")
        if "Scarcity Manipulation" in se_categories:
            indicators.append("Artificial scarcity tactics")
        if "Reciprocity Pressure" in se_categories:
            indicators.append("Guilt-based reciprocity pressure")
        if "Identity Attack" in se_categories:
            indicators.append("Ad-hominem or identity-based pressure")

        if domain != DomainType.GENERAL:
            indicators.append(
                f"Content targets {domain.value.lower()} domain — "
                f"elevated impact potential"
            )

        if density > 5.0:
            indicators.append(
                f"High manipulation density ({density:.1f}% of content)"
            )

        return indicators
