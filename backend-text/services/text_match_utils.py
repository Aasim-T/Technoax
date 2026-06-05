"""Reusable text matching helpers for word-level manipulation detection."""

import re
from dataclasses import dataclass

from services.pattern_catalog import Severity


@dataclass(frozen=True)
class TextSpanMatch:
    """A keyword occurrence with character offsets and severity in the source text."""

    word: str
    category: str
    severity: str
    start_index: int
    end_index: int


def find_all_spans(
    text: str,
    keyword: str,
    category: str,
    severity: Severity | str,
) -> list[TextSpanMatch]:
    """
    Find every case-insensitive occurrence of keyword in text.

    Returns spans using indices from the original text and the matched substring.
    """
    if not keyword or not text:
        return []

    severity_value = severity.value if isinstance(severity, Severity) else severity
    pattern = re.compile(re.escape(keyword), re.IGNORECASE)

    return [
        TextSpanMatch(
            word=text[match.start() : match.end()],
            category=category,
            severity=severity_value,
            start_index=match.start(),
            end_index=match.end(),
        )
        for match in pattern.finditer(text)
    ]


def dedupe_spans(spans: list[TextSpanMatch]) -> list[TextSpanMatch]:
    """Remove duplicate spans that share the same start index and category."""
    seen: set[tuple[int, str]] = set()
    unique: list[TextSpanMatch] = []

    for span in sorted(spans, key=lambda s: (s.start_index, -len(s.word))):
        key = (span.start_index, span.category)
        if key in seen:
            continue
        seen.add(key)
        unique.append(span)

    return unique
