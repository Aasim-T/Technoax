"""Social engineering pattern detection module.

Detects authority impersonation, reciprocity pressure, scarcity manipulation,
and social proof abuse — manipulation tactics not covered by the existing
pattern catalog. Produces TextSpanMatch objects compatible with the existing
detection pipeline.
"""

import re
import logging
from dataclasses import dataclass
from enum import Enum

from services.text_match_utils import TextSpanMatch

logger = logging.getLogger(__name__)


class SocialEngineeringCategory(str, Enum):
    """Social engineering manipulation sub-categories."""

    AUTHORITY_IMPERSONATION = "Authority Impersonation"
    RECIPROCITY_PRESSURE = "Reciprocity Pressure"
    SCARCITY_MANIPULATION = "Scarcity Manipulation"
    SOCIAL_PROOF_ABUSE = "Social Proof Abuse"
    IDENTITY_ATTACK = "Identity Attack"
    BANDWAGON_PRESSURE = "Bandwagon Pressure"


class SESeverity(str, Enum):
    """Severity levels for social engineering signals."""

    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


@dataclass(frozen=True)
class SEPatternEntry:
    """A social engineering detection pattern with category and severity."""

    phrase: str
    category: SocialEngineeringCategory
    severity: SESeverity


# ---------------------------------------------------------------------------
# Social Engineering Pattern Database
# ---------------------------------------------------------------------------

_AUTHORITY_PATTERNS = (
    SEPatternEntry("as a doctor", SocialEngineeringCategory.AUTHORITY_IMPERSONATION, SESeverity.HIGH),
    SEPatternEntry("as a scientist", SocialEngineeringCategory.AUTHORITY_IMPERSONATION, SESeverity.HIGH),
    SEPatternEntry("as an expert", SocialEngineeringCategory.AUTHORITY_IMPERSONATION, SESeverity.HIGH),
    SEPatternEntry("verified by scientists", SocialEngineeringCategory.AUTHORITY_IMPERSONATION, SESeverity.HIGH),
    SEPatternEntry("according to experts", SocialEngineeringCategory.AUTHORITY_IMPERSONATION, SESeverity.MEDIUM),
    SEPatternEntry("research proves", SocialEngineeringCategory.AUTHORITY_IMPERSONATION, SESeverity.MEDIUM),
    SEPatternEntry("studies show", SocialEngineeringCategory.AUTHORITY_IMPERSONATION, SESeverity.LOW),
    SEPatternEntry("experts agree", SocialEngineeringCategory.AUTHORITY_IMPERSONATION, SESeverity.MEDIUM),
    SEPatternEntry("doctors recommend", SocialEngineeringCategory.AUTHORITY_IMPERSONATION, SESeverity.MEDIUM),
    SEPatternEntry("harvard study", SocialEngineeringCategory.AUTHORITY_IMPERSONATION, SESeverity.MEDIUM),
    SEPatternEntry("stanford research", SocialEngineeringCategory.AUTHORITY_IMPERSONATION, SESeverity.MEDIUM),
    SEPatternEntry("fda approved", SocialEngineeringCategory.AUTHORITY_IMPERSONATION, SESeverity.MEDIUM),
    SEPatternEntry("clinically proven", SocialEngineeringCategory.AUTHORITY_IMPERSONATION, SESeverity.MEDIUM),
    SEPatternEntry("scientifically proven", SocialEngineeringCategory.AUTHORITY_IMPERSONATION, SESeverity.HIGH),
    SEPatternEntry("government official", SocialEngineeringCategory.AUTHORITY_IMPERSONATION, SESeverity.MEDIUM),
    SEPatternEntry("insider knowledge", SocialEngineeringCategory.AUTHORITY_IMPERSONATION, SESeverity.HIGH),
    SEPatternEntry("insider information", SocialEngineeringCategory.AUTHORITY_IMPERSONATION, SESeverity.HIGH),
)

_RECIPROCITY_PATTERNS = (
    SEPatternEntry("you owe", SocialEngineeringCategory.RECIPROCITY_PRESSURE, SESeverity.HIGH),
    SEPatternEntry("return the favor", SocialEngineeringCategory.RECIPROCITY_PRESSURE, SESeverity.HIGH),
    SEPatternEntry("we gave you", SocialEngineeringCategory.RECIPROCITY_PRESSURE, SESeverity.MEDIUM),
    SEPatternEntry("after everything", SocialEngineeringCategory.RECIPROCITY_PRESSURE, SESeverity.MEDIUM),
    SEPatternEntry("the least you can do", SocialEngineeringCategory.RECIPROCITY_PRESSURE, SESeverity.HIGH),
    SEPatternEntry("don't be ungrateful", SocialEngineeringCategory.RECIPROCITY_PRESSURE, SESeverity.HIGH),
    SEPatternEntry("we trusted you", SocialEngineeringCategory.RECIPROCITY_PRESSURE, SESeverity.MEDIUM),
    SEPatternEntry("do your part", SocialEngineeringCategory.RECIPROCITY_PRESSURE, SESeverity.MEDIUM),
)

_SCARCITY_PATTERNS = (
    SEPatternEntry("only a few left", SocialEngineeringCategory.SCARCITY_MANIPULATION, SESeverity.HIGH),
    SEPatternEntry("selling out fast", SocialEngineeringCategory.SCARCITY_MANIPULATION, SESeverity.HIGH),
    SEPatternEntry("limited supply", SocialEngineeringCategory.SCARCITY_MANIPULATION, SESeverity.HIGH),
    SEPatternEntry("while supplies last", SocialEngineeringCategory.SCARCITY_MANIPULATION, SESeverity.MEDIUM),
    SEPatternEntry("last chance", SocialEngineeringCategory.SCARCITY_MANIPULATION, SESeverity.HIGH),
    SEPatternEntry("once in a lifetime", SocialEngineeringCategory.SCARCITY_MANIPULATION, SESeverity.HIGH),
    SEPatternEntry("exclusive offer", SocialEngineeringCategory.SCARCITY_MANIPULATION, SESeverity.MEDIUM),
    SEPatternEntry("exclusive access", SocialEngineeringCategory.SCARCITY_MANIPULATION, SESeverity.MEDIUM),
    SEPatternEntry("spots are filling up", SocialEngineeringCategory.SCARCITY_MANIPULATION, SESeverity.HIGH),
    SEPatternEntry("won't last long", SocialEngineeringCategory.SCARCITY_MANIPULATION, SESeverity.MEDIUM),
    SEPatternEntry("almost gone", SocialEngineeringCategory.SCARCITY_MANIPULATION, SESeverity.MEDIUM),
    SEPatternEntry("running out", SocialEngineeringCategory.SCARCITY_MANIPULATION, SESeverity.MEDIUM),
)

_SOCIAL_PROOF_PATTERNS = (
    SEPatternEntry("everyone is doing", SocialEngineeringCategory.SOCIAL_PROOF_ABUSE, SESeverity.HIGH),
    SEPatternEntry("millions already", SocialEngineeringCategory.SOCIAL_PROOF_ABUSE, SESeverity.HIGH),
    SEPatternEntry("trending now", SocialEngineeringCategory.SOCIAL_PROOF_ABUSE, SESeverity.MEDIUM),
    SEPatternEntry("going viral", SocialEngineeringCategory.SOCIAL_PROOF_ABUSE, SESeverity.MEDIUM),
    SEPatternEntry("people are switching", SocialEngineeringCategory.SOCIAL_PROOF_ABUSE, SESeverity.MEDIUM),
    SEPatternEntry("thousands have already", SocialEngineeringCategory.SOCIAL_PROOF_ABUSE, SESeverity.HIGH),
    SEPatternEntry("join the movement", SocialEngineeringCategory.SOCIAL_PROOF_ABUSE, SESeverity.MEDIUM),
    SEPatternEntry("don't be left behind", SocialEngineeringCategory.SOCIAL_PROOF_ABUSE, SESeverity.HIGH),
    SEPatternEntry("everyone knows", SocialEngineeringCategory.SOCIAL_PROOF_ABUSE, SESeverity.MEDIUM),
    SEPatternEntry("most people", SocialEngineeringCategory.SOCIAL_PROOF_ABUSE, SESeverity.LOW),
    SEPatternEntry("the majority agrees", SocialEngineeringCategory.SOCIAL_PROOF_ABUSE, SESeverity.MEDIUM),
)

_IDENTITY_ATTACK_PATTERNS = (
    SEPatternEntry("only fools", SocialEngineeringCategory.IDENTITY_ATTACK, SESeverity.HIGH),
    SEPatternEntry("you're naive", SocialEngineeringCategory.IDENTITY_ATTACK, SESeverity.HIGH),
    SEPatternEntry("wake up sheeple", SocialEngineeringCategory.IDENTITY_ATTACK, SESeverity.HIGH),
    SEPatternEntry("open your eyes", SocialEngineeringCategory.IDENTITY_ATTACK, SESeverity.MEDIUM),
    SEPatternEntry("if you're smart", SocialEngineeringCategory.IDENTITY_ATTACK, SESeverity.MEDIUM),
    SEPatternEntry("only an idiot", SocialEngineeringCategory.IDENTITY_ATTACK, SESeverity.HIGH),
    SEPatternEntry("think for yourself", SocialEngineeringCategory.IDENTITY_ATTACK, SESeverity.LOW),
    SEPatternEntry("stop being blind", SocialEngineeringCategory.IDENTITY_ATTACK, SESeverity.HIGH),
)

_BANDWAGON_PATTERNS = (
    SEPatternEntry("everybody agrees", SocialEngineeringCategory.BANDWAGON_PRESSURE, SESeverity.HIGH),
    SEPatternEntry("no one disagrees", SocialEngineeringCategory.BANDWAGON_PRESSURE, SESeverity.HIGH),
    SEPatternEntry("it's common knowledge", SocialEngineeringCategory.BANDWAGON_PRESSURE, SESeverity.MEDIUM),
    SEPatternEntry("as we all know", SocialEngineeringCategory.BANDWAGON_PRESSURE, SESeverity.MEDIUM),
    SEPatternEntry("any reasonable person", SocialEngineeringCategory.BANDWAGON_PRESSURE, SESeverity.MEDIUM),
    SEPatternEntry("smart people know", SocialEngineeringCategory.BANDWAGON_PRESSURE, SESeverity.MEDIUM),
)

# Combined sorted database (longest phrases first for greedy matching)
SOCIAL_ENGINEERING_PATTERNS: tuple[SEPatternEntry, ...] = tuple(
    sorted(
        (
            *_AUTHORITY_PATTERNS,
            *_RECIPROCITY_PATTERNS,
            *_SCARCITY_PATTERNS,
            *_SOCIAL_PROOF_PATTERNS,
            *_IDENTITY_ATTACK_PATTERNS,
            *_BANDWAGON_PATTERNS,
        ),
        key=lambda e: len(e.phrase),
        reverse=True,
    )
)


@dataclass(frozen=True)
class SocialEngineeringResult:
    """Result of social engineering pattern detection."""

    detected_categories: list[str]
    spans: list[TextSpanMatch]
    signal_count: int
    severity_breakdown: dict[str, int]  # severity → count


class SocialEngineeringDetector:
    """
    Detects social engineering manipulation patterns in text.

    Produces TextSpanMatch objects fully compatible with the existing
    manipulation detection pipeline for seamless integration.
    """

    def detect(self, text: str) -> SocialEngineeringResult:
        """
        Scan text for social engineering indicators.

        Returns detected category labels and character-level span matches
        compatible with the existing heatmap pipeline.
        """
        if not text:
            return SocialEngineeringResult(
                detected_categories=[],
                spans=[],
                signal_count=0,
                severity_breakdown={},
            )

        all_spans: list[TextSpanMatch] = []

        for entry in SOCIAL_ENGINEERING_PATTERNS:
            spans = self._find_pattern_spans(text, entry)
            all_spans.extend(spans)

        # Deduplicate by start index + category
        deduped = self._dedupe_spans(all_spans)

        # Extract unique categories preserving order
        categories = self._unique_categories(deduped)

        # Severity breakdown
        severity_counts: dict[str, int] = {}
        for span in deduped:
            severity_counts[span.severity] = severity_counts.get(span.severity, 0) + 1

        return SocialEngineeringResult(
            detected_categories=categories,
            spans=deduped,
            signal_count=len(deduped),
            severity_breakdown=severity_counts,
        )

    @staticmethod
    def _find_pattern_spans(text: str, entry: SEPatternEntry) -> list[TextSpanMatch]:
        """Find all case-insensitive occurrences of a pattern phrase."""
        if not entry.phrase:
            return []

        pattern = re.compile(re.escape(entry.phrase), re.IGNORECASE)
        return [
            TextSpanMatch(
                word=text[match.start():match.end()],
                category=entry.category.value,
                severity=entry.severity.value,
                start_index=match.start(),
                end_index=match.end(),
            )
            for match in pattern.finditer(text)
        ]

    @staticmethod
    def _dedupe_spans(spans: list[TextSpanMatch]) -> list[TextSpanMatch]:
        """Remove duplicate spans by start index + category (longest match wins)."""
        seen: set[tuple[int, str]] = set()
        unique: list[TextSpanMatch] = []

        for span in sorted(spans, key=lambda s: (s.start_index, -len(s.word))):
            key = (span.start_index, span.category)
            if key not in seen:
                seen.add(key)
                unique.append(span)

        return unique

    @staticmethod
    def _unique_categories(spans: list[TextSpanMatch]) -> list[str]:
        """Preserve first-seen category order."""
        seen: set[str] = set()
        ordered: list[str] = []
        for span in spans:
            if span.category not in seen:
                seen.add(span.category)
                ordered.append(span.category)
        return ordered
