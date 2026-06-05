"""FastAPI router for the Audio Authenticity Intelligence Engine.

Exposes: POST /analyze-audio

Accepts multipart/form-data with an audio_file field.
Supported formats: mp3, wav, m4a, flac
Maximum size: 50 MB

This router is completely additive — it does NOT touch any existing
Technoax routes, services, or models.
"""

import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse

from config.settings import Settings, get_settings
from schemas.audio_schema import AudioAnalysisResponse
from services.audio_service import AudioService, AudioServiceError, get_audio_service
from utils.audio_utils import (
    AudioValidationError,
    delete_temp_file,
    save_temp_audio,
    validate_audio_file,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Audio Analysis"])


# ── Dependency ──────────────────────────────────────────────────────────────


def _get_audio_service(settings: Settings = Depends(get_settings)) -> AudioService:
    """Dependency: return the cached AudioService singleton."""
    return get_audio_service(settings)


# ── Endpoint ────────────────────────────────────────────────────────────────


@router.post(
    "/analyze-audio",
    response_model=AudioAnalysisResponse,
    summary="Audio Authenticity Intelligence — Detect AI-generated audio",
    description=(
        "Upload an audio file (mp3, wav, m4a, flac — max 50 MB) and receive a full "
        "AI authenticity report. The engine runs speech-to-text transcription, "
        "acoustic feature extraction, heuristic AI detection scoring, Gemini-powered "
        "explainability, and transcript trust analysis using the existing Technoax "
        "intelligence pipeline."
    ),
    response_description="Full audio authenticity analysis including AI probability, classification, transcript, and explainability.",
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "description": "Invalid or empty audio file",
            "content": {
                "application/json": {
                    "example": {"detail": "Audio file is empty."}
                }
            },
        },
        status.HTTP_413_REQUEST_ENTITY_TOO_LARGE: {
            "description": "File exceeds 50 MB limit",
            "content": {
                "application/json": {
                    "example": {"detail": "File size 55.2 MB exceeds the 50 MB limit."}
                }
            },
        },
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE: {
            "description": "Unsupported audio format",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Unsupported file format '.ogg'. Accepted formats: .flac, .m4a, .mp3, .wav."
                    }
                }
            },
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "description": "Audio could not be processed (corrupted file or transcription failure)",
            "content": {
                "application/json": {
                    "example": {"detail": "Speech-to-text transcription failed: [reason]"}
                }
            },
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Internal server error",
            "content": {
                "application/json": {
                    "example": {"detail": "Audio analysis pipeline failed."}
                }
            },
        },
    },
)
async def analyze_audio(
    audio_file: UploadFile = File(
        ...,
        description="Audio file to analyze. Supported formats: mp3, wav, m4a, flac. Max size: 50 MB.",
    ),
    audio_service: AudioService = Depends(_get_audio_service),
) -> AudioAnalysisResponse:
    """
    Analyze uploaded audio for AI generation authenticity.

    **Pipeline**:
    1. Validate file format and size
    2. Speech-to-Text transcription (faster-whisper)
    3. Acoustic feature extraction (librosa)
    4. Heuristic AI audio detection scoring
    5. Gemini-powered audio explainability
    6. Transcript trust analysis (existing Technoax engines)

    **Probability scale**:
    - `0-30` → Likely Human
    - `31-69` → Uncertain
    - `70-100` → Likely AI Generated
    """
    filename = audio_file.filename or "audio_upload"
    content_type = audio_file.content_type or ""
    temp_path: str | None = None

    try:
        # ── Read file into memory ─────────────────────────────────────
        logger.info("Received audio upload: filename='%s' content_type='%s'", filename, content_type)
        audio_bytes = await audio_file.read()

        if not audio_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Audio file is empty.",
            )

        file_size = len(audio_bytes)
        logger.info("Audio file size: %.2f MB", file_size / (1024 * 1024))

        # ── Validate ──────────────────────────────────────────────────
        try:
            validate_audio_file(
                filename=filename,
                content_type=content_type,
                file_size=file_size,
            )
        except AudioValidationError as exc:
            raise HTTPException(
                status_code=exc.http_status,
                detail=str(exc),
            ) from exc

        # ── Save to temp file ─────────────────────────────────────────
        from pathlib import Path
        suffix = Path(filename).suffix.lower()
        temp_path = save_temp_audio(audio_bytes, suffix=suffix)

        # ── Run analysis pipeline ─────────────────────────────────────
        logger.info("Starting audio analysis pipeline for: %s", filename)
        result = audio_service.analyze(temp_path)

        logger.info(
            "Audio analysis complete: probability=%d classification='%s'",
            result.audio_ai_probability,
            result.classification,
        )
        return result

    except HTTPException:
        raise

    except AudioServiceError as exc:
        logger.warning("Audio service error: %s", exc)
        raise HTTPException(
            status_code=exc.http_status,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        logger.exception("Unexpected error in audio analysis: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Audio analysis pipeline encountered an unexpected error.",
        ) from exc

    finally:
        # Always clean up temp file
        if temp_path:
            delete_temp_file(temp_path)
        # Always close the upload file
        await audio_file.close()
