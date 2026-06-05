"""In-memory analytics and metrics tracking for Technoax.

Provides real-time observability into analysis patterns, Gemini health,
and system performance. Extensible to persistent storage for production.
"""

import logging
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from threading import Lock

logger = logging.getLogger(__name__)


@dataclass
class GeminiHealthMetrics:
    """Gemini API health and performance metrics."""

    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    quota_errors: int = 0
    average_latency_ms: float = 0.0
    last_call_time: float | None = None
    circuit_breaker_state: str = "closed"
    circuit_breaker_trips: int = 0

    @property
    def success_rate(self) -> float:
        if self.total_calls == 0:
            return 0.0
        return round(self.successful_calls / self.total_calls * 100, 1)


@dataclass
class AnalysisSummary:
    """A recorded analysis result summary for tracking."""

    timestamp: float
    trust_score: int
    risk_level: str
    detected_patterns: list[str]
    matched_word_count: int
    domain: str
    confidence_score: int
    ai_probability: int
    text_length: int
    gemini_used: bool
    latency_ms: float


@dataclass
class AnalyticsDashboard:
    """Complete analytics dashboard payload."""

    # Overall stats
    total_analyses: int
    analyses_last_hour: int
    average_trust_score: float
    median_trust_score: int

    # Risk distribution
    risk_distribution: dict[str, int]

    # Pattern frequency
    top_patterns: list[dict[str, int | str]]
    pattern_frequency: dict[str, int]

    # Domain distribution
    domain_distribution: dict[str, int]

    # AI probability stats
    average_ai_probability: float

    # Gemini health
    gemini_health: dict[str, object]

    # Performance
    average_latency_ms: float
    total_uptime_seconds: float

    # Recent analyses (last 10)
    recent_analyses: list[dict[str, object]]


class AnalyticsTracker:
    """
    Singleton in-memory analytics tracker.

    Thread-safe. Tracks per-request analysis results, Gemini health,
    and aggregate statistics for the analytics dashboard.

    For production, replace the in-memory store with a persistent backend
    (Redis, PostgreSQL, etc.) by subclassing.
    """

    _instance: "AnalyticsTracker | None" = None
    _lock = Lock()

    def __new__(cls) -> "AnalyticsTracker":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True

        self._analyses: list[AnalysisSummary] = []
        self._gemini_health = GeminiHealthMetrics()
        self._start_time = time.time()
        self._pattern_counter: Counter = Counter()
        self._domain_counter: Counter = Counter()
        self._risk_counter: Counter = Counter()
        self._data_lock = Lock()

        logger.info("AnalyticsTracker initialized")

    def record_analysis(
        self,
        trust_score: int,
        risk_level: str,
        detected_patterns: list[str],
        matched_word_count: int,
        domain: str = "General",
        confidence_score: int = 0,
        ai_probability: int = 0,
        text_length: int = 0,
        gemini_used: bool = False,
        latency_ms: float = 0.0,
    ) -> None:
        """Record a completed analysis for tracking."""
        summary = AnalysisSummary(
            timestamp=time.time(),
            trust_score=trust_score,
            risk_level=risk_level,
            detected_patterns=detected_patterns,
            matched_word_count=matched_word_count,
            domain=domain,
            confidence_score=confidence_score,
            ai_probability=ai_probability,
            text_length=text_length,
            gemini_used=gemini_used,
            latency_ms=latency_ms,
        )

        with self._data_lock:
            self._analyses.append(summary)

            # Update counters
            for pattern in detected_patterns:
                self._pattern_counter[pattern] += 1
            self._domain_counter[domain] += 1
            self._risk_counter[risk_level] += 1

            # Cap stored analyses at 10,000 to prevent memory bloat
            if len(self._analyses) > 10_000:
                self._analyses = self._analyses[-5_000:]

    def record_gemini_call(
        self,
        success: bool,
        latency_ms: float = 0.0,
        is_quota_error: bool = False,
    ) -> None:
        """Record a Gemini API call result."""
        with self._data_lock:
            self._gemini_health.total_calls += 1
            self._gemini_health.last_call_time = time.time()

            if success:
                self._gemini_health.successful_calls += 1
            else:
                self._gemini_health.failed_calls += 1
                if is_quota_error:
                    self._gemini_health.quota_errors += 1

            # Running average latency
            if self._gemini_health.total_calls == 1:
                self._gemini_health.average_latency_ms = latency_ms
            else:
                prev = self._gemini_health.average_latency_ms
                n = self._gemini_health.total_calls
                self._gemini_health.average_latency_ms = (
                    prev * (n - 1) + latency_ms
                ) / n

    def record_circuit_breaker_trip(self, state: str) -> None:
        """Record a circuit breaker state change."""
        with self._data_lock:
            self._gemini_health.circuit_breaker_state = state
            if state == "open":
                self._gemini_health.circuit_breaker_trips += 1

    def get_dashboard(self) -> AnalyticsDashboard:
        """Generate the complete analytics dashboard."""
        with self._data_lock:
            total = len(self._analyses)

            if total == 0:
                return self._empty_dashboard()

            # Calculate stats
            trust_scores = [a.trust_score for a in self._analyses]
            avg_trust = sum(trust_scores) / total
            sorted_scores = sorted(trust_scores)
            median_trust = sorted_scores[total // 2]

            # Analyses in the last hour
            one_hour_ago = time.time() - 3600
            recent_count = sum(
                1 for a in self._analyses if a.timestamp > one_hour_ago
            )

            # AI probability stats
            ai_probs = [a.ai_probability for a in self._analyses]
            avg_ai_prob = sum(ai_probs) / total if ai_probs else 0.0

            # Average latency
            latencies = [a.latency_ms for a in self._analyses if a.latency_ms > 0]
            avg_latency = sum(latencies) / len(latencies) if latencies else 0.0

            # Top patterns
            top_patterns = [
                {"pattern": pattern, "count": count}
                for pattern, count in self._pattern_counter.most_common(10)
            ]

            # Recent analyses (last 10)
            recent = [
                {
                    "trust_score": a.trust_score,
                    "risk_level": a.risk_level,
                    "domain": a.domain,
                    "patterns": a.detected_patterns,
                    "ai_probability": a.ai_probability,
                    "text_length": a.text_length,
                    "latency_ms": round(a.latency_ms, 1),
                    "timestamp": a.timestamp,
                }
                for a in self._analyses[-10:]
            ]

            return AnalyticsDashboard(
                total_analyses=total,
                analyses_last_hour=recent_count,
                average_trust_score=round(avg_trust, 1),
                median_trust_score=median_trust,
                risk_distribution=dict(self._risk_counter),
                top_patterns=top_patterns,
                pattern_frequency=dict(self._pattern_counter),
                domain_distribution=dict(self._domain_counter),
                average_ai_probability=round(avg_ai_prob, 1),
                gemini_health={
                    "total_calls": self._gemini_health.total_calls,
                    "success_rate": self._gemini_health.success_rate,
                    "failed_calls": self._gemini_health.failed_calls,
                    "quota_errors": self._gemini_health.quota_errors,
                    "average_latency_ms": round(
                        self._gemini_health.average_latency_ms, 1
                    ),
                    "circuit_breaker_state": self._gemini_health.circuit_breaker_state,
                    "circuit_breaker_trips": self._gemini_health.circuit_breaker_trips,
                },
                average_latency_ms=round(avg_latency, 1),
                total_uptime_seconds=round(time.time() - self._start_time, 1),
                recent_analyses=recent,
            )

    def get_health_summary(self) -> dict[str, object]:
        """Return a lightweight health summary for the health endpoint."""
        with self._data_lock:
            return {
                "status": "healthy",
                "total_analyses": len(self._analyses),
                "uptime_seconds": round(time.time() - self._start_time, 1),
                "gemini": {
                    "total_calls": self._gemini_health.total_calls,
                    "success_rate": self._gemini_health.success_rate,
                    "circuit_breaker_state": self._gemini_health.circuit_breaker_state,
                    "circuit_breaker_trips": self._gemini_health.circuit_breaker_trips,
                    "quota_errors": self._gemini_health.quota_errors,
                },
            }

    def _empty_dashboard(self) -> AnalyticsDashboard:
        """Return an empty dashboard when no analyses have been recorded."""
        return AnalyticsDashboard(
            total_analyses=0,
            analyses_last_hour=0,
            average_trust_score=0.0,
            median_trust_score=0,
            risk_distribution={},
            top_patterns=[],
            pattern_frequency={},
            domain_distribution={},
            average_ai_probability=0.0,
            gemini_health={
                "total_calls": 0,
                "success_rate": 0.0,
                "failed_calls": 0,
                "quota_errors": 0,
                "average_latency_ms": 0.0,
                "circuit_breaker_state": "closed",
                "circuit_breaker_trips": 0,
            },
            average_latency_ms=0.0,
            total_uptime_seconds=round(time.time() - self._start_time, 1),
            recent_analyses=[],
        )


def get_analytics_tracker() -> AnalyticsTracker:
    """Return the singleton analytics tracker."""
    return AnalyticsTracker()
