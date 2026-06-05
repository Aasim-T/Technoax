"""
Technoax — Explainable Digital Trust Platform API.

Run locally:
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""

import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config.settings import get_settings
from models.response_models import HealthResponse
from routes.analyze import router as analyze_router
from routes.enhanced_analyze import router as enhanced_analyze_router
from routes.analytics import router as analytics_router
from routes.audio_routes import router as audio_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    logger.info("Starting %s v%s", settings.app_name, settings.app_version)
    if settings.is_gemini_configured:
        logger.info(
            "Gemini integration active (model=%s, SDK=google-genai)",
            settings.gemini_model,
        )
    else:
        logger.warning(
            "GEMINI_API_KEY is not set in backend/.env — hybrid scoring and AI explainability "
            "will use rule-based fallback only"
        )
    yield
    logger.info("Shutting down %s", settings.app_name)


def create_app() -> FastAPI:
    """Application factory for Technoax."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        description=(
            "Technoax analyzes text for emotional manipulation, fear tactics, "
            "urgency cues, clickbait, and conspiracy framing. Returns trust score, "
            "risk level, word-level matches, manipulation heatmap indices, and AI explainability."
        ),
        version=settings.app_version,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(analyze_router)
    app.include_router(enhanced_analyze_router)
    app.include_router(analytics_router)
    app.include_router(audio_router)

    @app.get("/health", response_model=HealthResponse, tags=["Health"])
    async def health_check() -> HealthResponse:
        """Service health probe."""
        return HealthResponse(
            status="ok",
            service=settings.app_name,
            version=settings.app_version,
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        _request: Request,
        exc: Exception,
    ) -> JSONResponse:
        logger.exception("Unhandled error: %s", exc)
        return JSONResponse(
            status_code=500,
            content={"detail": "An unexpected server error occurred."},
        )

    return app


app = create_app()
