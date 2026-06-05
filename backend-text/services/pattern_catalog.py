"""Central catalog of manipulation patterns, severities, and scoring penalties."""

from dataclasses import dataclass
from enum import Enum


class ManipulationCategory(str, Enum):
    """Supported manipulation pattern categories."""

    FEAR = "Fear"
    URGENCY = "Urgency"
    CLICKBAIT = "Clickbait"
    EMOTIONAL_TRIGGER = "Emotional Trigger"
    CONSPIRACY = "Conspiracy"


class Severity(str, Enum):
    """Manipulation signal severity for scoring and heatmap visualization."""

    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


PENALTY_BY_SEVERITY: dict[Severity, int] = {
    Severity.LOW: 5,
    Severity.MEDIUM: 10,
    Severity.HIGH: 20,
}

# Multi-match scoring adjustments
MULTI_CATEGORY_PENALTY = 10
REPEAT_MATCH_PENALTY = 5
CONSPIRACY_URGENCY_COMBO_PENALTY = 15

BASE_TRUST_SCORE = 100


@dataclass(frozen=True)
class PatternEntry:
    """A detectable manipulation phrase with category and severity."""

    phrase: str
    category: ManipulationCategory
    severity: Severity


def _entries(
    category: ManipulationCategory,
    phrases: tuple[tuple[str, Severity], ...],
) -> tuple[PatternEntry, ...]:
    return tuple(
        PatternEntry(phrase=phrase, category=category, severity=severity)
        for phrase, severity in phrases
    )


# --- Fear ---
_FEAR_ENTRIES = _entries(
    ManipulationCategory.FEAR,
    (
        ("cancer", Severity.HIGH),
        ("deadly", Severity.HIGH),
        ("dangerous", Severity.HIGH),
        ("virus", Severity.HIGH),
        ("toxic", Severity.HIGH),
        ("harmful", Severity.HIGH),
        ("poison", Severity.HIGH),
        ("disaster", Severity.HIGH),
        ("panic", Severity.HIGH),
        ("fatal", Severity.HIGH),
        ("emergency", Severity.HIGH),
        ("unsafe", Severity.HIGH),
        ("danger", Severity.HIGH),
        ("threat", Severity.HIGH),
        ("fear", Severity.MEDIUM),
        ("risk", Severity.MEDIUM),
        ("warning", Severity.MEDIUM),
    ),
)

# --- Urgency ---
_URGENCY_ENTRIES = _entries(
    ManipulationCategory.URGENCY,
    (
        ("instant action required", Severity.HIGH),
        ("share immediately", Severity.HIGH),
        ("before it's deleted", Severity.HIGH),
        ("before it's too late", Severity.HIGH),
        ("act now", Severity.HIGH),
        ("share now", Severity.HIGH),
        ("right now", Severity.HIGH),
        ("limited time", Severity.MEDIUM),
        ("don't wait", Severity.MEDIUM),
        ("immediately", Severity.MEDIUM),
        ("urgent", Severity.MEDIUM),
    ),
)

# --- Clickbait ---
_CLICKBAIT_ENTRIES = _entries(
    ManipulationCategory.CLICKBAIT,
    (
        ("you won't believe", Severity.HIGH),
        ("miracle cure", Severity.HIGH),
        ("mind-blowing", Severity.HIGH),
        ("jaw-dropping", Severity.HIGH),
        ("viral truth", Severity.HIGH),
        ("what happened next", Severity.HIGH),
        ("shocking", Severity.MEDIUM),
        ("unbelievable", Severity.MEDIUM),
        ("secret", Severity.MEDIUM),
        ("hidden", Severity.MEDIUM),
        ("exposed", Severity.MEDIUM),
        ("breaking", Severity.MEDIUM),
    ),
)

# --- Emotional manipulation ---
_EMOTIONAL_ENTRIES = _entries(
    ManipulationCategory.EMOTIONAL_TRIGGER,
    (
        ("protect your family", Severity.HIGH),
        ("save your children", Severity.HIGH),
        ("share to save lives", Severity.HIGH),
        ("for the sake of your family", Severity.HIGH),
        ("your loved ones", Severity.MEDIUM),
        ("care about your family", Severity.MEDIUM),
        ("if you truly care", Severity.MEDIUM),
        ("everyone must know", Severity.MEDIUM),
        ("don't ignore this", Severity.MEDIUM),
    ),
)

# --- Conspiracy (high vs medium framing) ---
_CONSPIRACY_ENTRIES = _entries(
    ManipulationCategory.CONSPIRACY,
    (
        ("they don't want you to know", Severity.HIGH),
        ("government hiding", Severity.HIGH),
        ("they are hiding", Severity.HIGH),
        ("silence this", Severity.HIGH),
        ("mainstream media won't tell you", Severity.HIGH),
        ("doctors hate this", Severity.HIGH),
        ("pharmaceutical companies", Severity.HIGH),
        ("classified evidence", Severity.HIGH),
        ("suppressed information", Severity.HIGH),
        ("deep state", Severity.HIGH),
        ("what they hide from you", Severity.HIGH),
        ("hidden truth", Severity.MEDIUM),
        ("covering it up", Severity.MEDIUM),
        ("secret cure", Severity.MEDIUM),
        ("censored", Severity.MEDIUM),
        ("trying to silence", Severity.MEDIUM),
    ),
)

PATTERN_DATABASE: tuple[PatternEntry, ...] = tuple(
    sorted(
        (
            *_FEAR_ENTRIES,
            *_URGENCY_ENTRIES,
            *_CLICKBAIT_ENTRIES,
            *_EMOTIONAL_ENTRIES,
            *_CONSPIRACY_ENTRIES,
        ),
        key=lambda entry: len(entry.phrase),
        reverse=True,
    )
)

# Legacy category-level severity fallback for heatmap helpers
SEVERITY_BY_CATEGORY: dict[str, Severity] = {
    ManipulationCategory.FEAR.value: Severity.HIGH,
    ManipulationCategory.URGENCY.value: Severity.MEDIUM,
    ManipulationCategory.CLICKBAIT.value: Severity.MEDIUM,
    ManipulationCategory.EMOTIONAL_TRIGGER.value: Severity.LOW,
    ManipulationCategory.CONSPIRACY.value: Severity.HIGH,
}

# Backward-compatible category keyword map (used by documentation / tests)
CATEGORY_KEYWORDS: dict[ManipulationCategory, tuple[str, ...]] = {
    category: tuple(
        entry.phrase
        for entry in PATTERN_DATABASE
        if entry.category == category
    )
    for category in ManipulationCategory
}
