"""Utility functions for audio file validation and temp-file management.

This module is self-contained and does not import from any existing
Technoax service modules. It handles:
  - File format validation (extension + size)
  - Safe temporary file creation and cleanup
"""

import logging
import os
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)

# Supported audio MIME types and their canonical extensions
SUPPORTED_EXTENSIONS: frozenset[str] = frozenset({".mp3", ".wav", ".m4a", ".flac"})

SUPPORTED_CONTENT_TYPES: frozenset[str] = frozenset({
    "audio/mpeg",
    "audio/mp3",
    "audio/wav",
    "audio/x-wav",
    "audio/wave",
    "audio/m4a",
    "audio/mp4",
    "audio/x-m4a",
    "audio/flac",
    "audio/x-flac",
    # browsers sometimes report generic binary
    "application/octet-stream",
})

MAX_FILE_SIZE_BYTES: int = 50 * 1024 * 1024  # 50 MB


class AudioValidationError(Exception):
    """Raised when an uploaded audio file fails validation."""

    def __init__(self, message: str, http_status: int = 422) -> None:
        super().__init__(message)
        self.http_status = http_status


def validate_audio_file(filename: str, content_type: str, file_size: int) -> None:
    """
    Validate uploaded audio file metadata.

    Args:
        filename: Original filename (used for extension check).
        content_type: MIME type reported by the HTTP client.
        file_size: File size in bytes.

    Raises:
        AudioValidationError: With an appropriate HTTP status code.
    """
    # Size check
    if file_size > MAX_FILE_SIZE_BYTES:
        raise AudioValidationError(
            f"File size {file_size / (1024 * 1024):.1f} MB exceeds the 50 MB limit.",
            http_status=413,
        )

    # Extension check (primary guard, more reliable than MIME)
    ext = Path(filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise AudioValidationError(
            f"Unsupported file format '{ext}'. "
            f"Accepted formats: {', '.join(sorted(SUPPORTED_EXTENSIONS))}.",
            http_status=415,
        )

    # MIME type check (secondary; allow pass-through for octet-stream)
    if (
        content_type
        and content_type not in SUPPORTED_CONTENT_TYPES
        and not content_type.startswith("audio/")
    ):
        logger.warning(
            "Unexpected content-type '%s' for file '%s' — proceeding with extension check only.",
            content_type,
            filename,
        )


def save_temp_audio(data: bytes, suffix: str) -> str:
    """
    Write audio bytes to a named temporary file and return its path.

    The caller is responsible for deleting the file via ``delete_temp_file``.

    Args:
        data:   Raw audio bytes.
        suffix: File extension including dot (e.g. ".wav").

    Returns:
        Absolute path to the temporary file.
    """
    fd, path = tempfile.mkstemp(suffix=suffix, prefix="technoax_audio_")
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
    except Exception:
        os.unlink(path)
        raise

    logger.debug("Saved temp audio: %s (%d bytes)", path, len(data))
    return path


def delete_temp_file(path: str) -> None:
    """
    Safely delete a temporary file, suppressing errors if already gone.

    Args:
        path: Absolute path to the file to remove.
    """
    try:
        os.unlink(path)
        logger.debug("Deleted temp audio: %s", path)
    except FileNotFoundError:
        pass
    except OSError as exc:
        logger.warning("Could not delete temp file '%s': %s", path, exc)
