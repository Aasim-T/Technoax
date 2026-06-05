"""Rule-based word-level manipulation pattern detection."""

from dataclasses import dataclass

from services.pattern_catalog import PATTERN_DATABASE
from services.text_match_utils import TextSpanMatch, dedupe_spans, find_all_spans


@dataclass(frozen=True)
class DetectionResult:
    """Outcome of rule-based pattern detection."""

    detected_patterns: list[str]
    spans: list[TextSpanMatch]


class ManipulationDetector:
    """Detects manipulation patterns and locates matched words in source text."""

    def detect(self, text: str) -> DetectionResult:
        """
        Scan text for manipulation indicators across all supported categories.

        Returns detected category labels and character-level span matches for heatmaps.
        """
        all_spans: list[TextSpanMatch] = []

        for entry in PATTERN_DATABASE:
            label = entry.category.value
            all_spans.extend(
                find_all_spans(
                    text=text,
                    keyword=entry.phrase,
                    category=label,
                    severity=entry.severity,
                )
            )

        spans = dedupe_spans(all_spans)
        detected_patterns = self._unique_categories_in_order(spans)

        return DetectionResult(
            detected_patterns=detected_patterns,
            spans=spans,
        )

    @staticmethod
    def _unique_categories_in_order(spans: list[TextSpanMatch]) -> list[str]:
        """Preserve first-seen category order for stable API responses."""
        seen: set[str] = set()
        ordered: list[str] = []
        for span in spans:
            if span.category not in seen:
                seen.add(span.category)
                ordered.append(span.category)
        return ordered
