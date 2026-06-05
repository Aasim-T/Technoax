"""Builds manipulation heatmap payloads for frontend highlighting."""

from models.response_models import HeatmapWord, MatchedWord
from services.pattern_catalog import SEVERITY_BY_CATEGORY, Severity
from services.text_match_utils import TextSpanMatch


def severity_for_span(span: TextSpanMatch) -> str:
    """Resolve severity label for a matched span."""
    if span.severity:
        return span.severity
    return SEVERITY_BY_CATEGORY.get(span.category, Severity.MEDIUM).value


def spans_to_matched_words(spans: list[TextSpanMatch]) -> list[MatchedWord]:
    """Convert span matches to API matched-word entries (deduped by word + category)."""
    seen: set[tuple[str, str]] = set()
    results: list[MatchedWord] = []

    for span in sorted(spans, key=lambda s: s.start_index):
        key = (span.word.lower(), span.category)
        if key in seen:
            continue
        seen.add(key)
        results.append(
            MatchedWord(
                word=span.word,
                category=span.category,
                severity=severity_for_span(span),
            )
        )

    return results


def spans_to_heatmap(spans: list[TextSpanMatch]) -> list[HeatmapWord]:
    """Convert span matches to full heatmap entries with character offsets."""
    return [
        HeatmapWord(
            word=span.word,
            category=span.category,
            severity=severity_for_span(span),
            start_index=span.start_index,
            end_index=span.end_index,
        )
        for span in sorted(spans, key=lambda s: s.start_index)
    ]
