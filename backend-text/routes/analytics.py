"""Analytics and system health endpoints for Technoax.

Provides real-time observability into analysis patterns, Gemini health,
and system performance metrics.
"""

import logging

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from services.analytics_tracker import AnalyticsTracker, get_analytics_tracker
from services.resilient_client import get_gemini_circuit_breaker
from services.prompt_framework import get_prompt_registry

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get(
    "/dashboard",
    summary="Analytics dashboard with real-time metrics",
    description=(
        "Returns comprehensive analytics including analysis counts, trust score "
        "distributions, pattern frequency, domain breakdown, Gemini health, "
        "and recent analysis history."
    ),
)
async def analytics_dashboard(
    analytics: AnalyticsTracker = Depends(get_analytics_tracker),
) -> JSONResponse:
    """Full analytics dashboard with all tracked metrics."""
    dashboard = analytics.get_dashboard()
    return JSONResponse(content={
        "total_analyses": dashboard.total_analyses,
        "analyses_last_hour": dashboard.analyses_last_hour,
        "average_trust_score": dashboard.average_trust_score,
        "median_trust_score": dashboard.median_trust_score,
        "risk_distribution": dashboard.risk_distribution,
        "top_patterns": dashboard.top_patterns,
        "pattern_frequency": dashboard.pattern_frequency,
        "domain_distribution": dashboard.domain_distribution,
        "average_ai_probability": dashboard.average_ai_probability,
        "gemini_health": dashboard.gemini_health,
        "average_latency_ms": dashboard.average_latency_ms,
        "total_uptime_seconds": dashboard.total_uptime_seconds,
        "recent_analyses": dashboard.recent_analyses,
    })


@router.get(
    "/health",
    summary="System health and Gemini circuit breaker status",
    description=(
        "Returns lightweight health check including Gemini API availability, "
        "circuit breaker state, and system uptime."
    ),
)
async def system_health(
    analytics: AnalyticsTracker = Depends(get_analytics_tracker),
) -> JSONResponse:
    """System health with Gemini circuit breaker status."""
    health = analytics.get_health_summary()

    # Enrich with circuit breaker stats
    circuit_breaker = get_gemini_circuit_breaker()
    cb_stats = circuit_breaker.stats
    health["circuit_breaker"] = {
        "state": cb_stats.state.value,
        "consecutive_failures": cb_stats.consecutive_failures,
        "total_successes": cb_stats.total_successes,
        "total_failures": cb_stats.total_failures,
    }

    return JSONResponse(content=health)


@router.get(
    "/prompts",
    summary="List registered prompt templates",
    description="Returns all registered prompt templates with name, version, and description.",
)
async def list_prompt_templates() -> JSONResponse:
    """List all registered Gemini prompt templates."""
    registry = get_prompt_registry()
    templates = registry.list_templates()
    return JSONResponse(content={
        "templates": templates,
        "total": len(templates),
    })
