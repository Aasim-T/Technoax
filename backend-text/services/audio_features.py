"""Audio feature extraction engine using librosa.

Extracts acoustic and prosodic features from an audio file that are
used by the AI audio detection engine to classify speech as human
or AI/TTS generated. This module has NO dependency on existing
Technoax service modules.

Features extracted
------------------
- Pitch statistics (mean, std dev, variance)
- Energy statistics (RMS mean, variance)
- Speaking rate (estimated syllables / second)
- Pause distribution (pause count, pause ratio)
- Silence ratio
- MFCC features (mean per coefficient)
- Spectral centroid (mean)
- Spectral roll-off (mean)
- Zero crossing rate (mean)
- Voice stability index (inverse of pitch CV)
"""

import logging
from dataclasses import dataclass, field

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class AudioFeatures:
    """All acoustic features extracted from one audio file."""

    # ── Duration ───────────────────────────────────────────────────────
    duration_seconds: float = 0.0

    # ── Pitch ──────────────────────────────────────────────────────────
    pitch_mean: float = 0.0          # Hz
    pitch_std: float = 0.0           # Hz
    pitch_variance: float = 0.0      # Hz²
    pitch_cv: float = 0.0            # Coefficient of variation (std/mean)

    # ── Energy ─────────────────────────────────────────────────────────
    energy_mean: float = 0.0         # RMS energy mean
    energy_std: float = 0.0
    energy_variance: float = 0.0
    energy_cv: float = 0.0           # Coefficient of variation

    # ── Speaking Rate ──────────────────────────────────────────────────
    speaking_rate: float = 0.0       # Estimated syllables per second

    # ── Pauses / Silence ───────────────────────────────────────────────
    pause_count: int = 0
    pause_ratio: float = 0.0         # Fraction of total duration that is silence
    silence_ratio: float = 0.0       # Overall silence fraction

    # ── MFCC ───────────────────────────────────────────────────────────
    mfcc_means: list[float] = field(default_factory=list)   # Per-coefficient means
    mfcc_stds: list[float] = field(default_factory=list)    # Per-coefficient stds

    # ── Spectral ───────────────────────────────────────────────────────
    spectral_centroid_mean: float = 0.0   # Hz
    spectral_rolloff_mean: float = 0.0    # Hz

    # ── Zero Crossing Rate ─────────────────────────────────────────────
    zcr_mean: float = 0.0

    # ── Voice Stability ────────────────────────────────────────────────
    voice_stability: float = 0.0     # 0-1; higher = more stable/AI-like


class AudioFeatureExtractor:
    """
    Extracts acoustic features from an audio file using librosa.

    Designed to be instantiated once and reused across requests.
    All librosa calls are synchronous (CPU-bound).
    """

    # Silence threshold (dB below max energy)
    _SILENCE_THRESHOLD_DB: float = -40.0
    # Minimum silence duration to count as a "pause" (seconds)
    _MIN_PAUSE_DURATION_S: float = 0.15
    # Number of MFCC coefficients to compute
    _N_MFCC: int = 13

    def extract(self, audio_path: str) -> AudioFeatures:
        """
        Load audio and compute all features.

        Args:
            audio_path: Absolute path to the audio file.

        Returns:
            AudioFeatures dataclass with all extracted metrics.

        Raises:
            RuntimeError: If audio loading or feature extraction fails.
        """
        try:
            import librosa  # deferred import so the module loads even if librosa missing
        except ImportError as exc:
            raise RuntimeError(
                "librosa is required for audio feature extraction. "
                "Install it with: pip install librosa"
            ) from exc

        try:
            logger.info("Loading audio file: %s", audio_path)
            # Load mono, 22 050 Hz
            y, sr = librosa.load(audio_path, sr=22050, mono=True)
        except Exception as exc:
            raise RuntimeError(f"Failed to load audio file: {exc}") from exc

        features = AudioFeatures()
        features.duration_seconds = float(len(y) / sr)

        try:
            features = self._extract_pitch(y, sr, features, librosa)
            features = self._extract_energy(y, sr, features, librosa)
            features = self._extract_spectral(y, sr, features, librosa)
            features = self._extract_mfcc(y, sr, features, librosa)
            features = self._extract_zcr(y, features, librosa)
            features = self._extract_silence(y, sr, features, librosa)
            features = self._compute_voice_stability(features)
        except Exception as exc:
            logger.warning("Partial feature extraction failure: %s — using defaults", exc)

        return features

    # ── Pitch ──────────────────────────────────────────────────────────

    @staticmethod
    def _extract_pitch(
        y: np.ndarray,
        sr: int,
        features: AudioFeatures,
        librosa,
    ) -> AudioFeatures:
        """Use librosa's pYIN algorithm for reliable F0 estimation."""
        try:
            f0, voiced_flag, _ = librosa.pyin(
                y,
                fmin=librosa.note_to_hz("C2"),   # ~65 Hz
                fmax=librosa.note_to_hz("C7"),   # ~2093 Hz
                sr=sr,
            )
            voiced_f0 = f0[voiced_flag & ~np.isnan(f0)] if f0 is not None else np.array([])

            if len(voiced_f0) > 1:
                features.pitch_mean = float(np.mean(voiced_f0))
                features.pitch_std = float(np.std(voiced_f0))
                features.pitch_variance = float(np.var(voiced_f0))
                if features.pitch_mean > 0:
                    features.pitch_cv = features.pitch_std / features.pitch_mean
            else:
                logger.debug("No voiced frames detected — pitch features set to 0")
        except Exception as exc:
            logger.debug("Pitch extraction warning: %s", exc)

        return features

    # ── Energy ─────────────────────────────────────────────────────────

    @staticmethod
    def _extract_energy(
        y: np.ndarray,
        sr: int,
        features: AudioFeatures,
        librosa,
    ) -> AudioFeatures:
        """RMS energy per frame."""
        rms = librosa.feature.rms(y=y)[0]
        if len(rms) > 0:
            features.energy_mean = float(np.mean(rms))
            features.energy_std = float(np.std(rms))
            features.energy_variance = float(np.var(rms))
            if features.energy_mean > 0:
                features.energy_cv = features.energy_std / features.energy_mean
        return features

    # ── Spectral ───────────────────────────────────────────────────────

    @staticmethod
    def _extract_spectral(
        y: np.ndarray,
        sr: int,
        features: AudioFeatures,
        librosa,
    ) -> AudioFeatures:
        """Spectral centroid and roll-off."""
        centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
        if len(centroid) > 0:
            features.spectral_centroid_mean = float(np.mean(centroid))
        if len(rolloff) > 0:
            features.spectral_rolloff_mean = float(np.mean(rolloff))
        return features

    # ── MFCC ───────────────────────────────────────────────────────────

    def _extract_mfcc(
        self,
        y: np.ndarray,
        sr: int,
        features: AudioFeatures,
        librosa,
    ) -> AudioFeatures:
        """Mel-frequency cepstral coefficients."""
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=self._N_MFCC)
        features.mfcc_means = [float(np.mean(c)) for c in mfcc]
        features.mfcc_stds = [float(np.std(c)) for c in mfcc]
        return features

    # ── ZCR ────────────────────────────────────────────────────────────

    @staticmethod
    def _extract_zcr(
        y: np.ndarray,
        features: AudioFeatures,
        librosa,
    ) -> AudioFeatures:
        """Zero crossing rate."""
        zcr = librosa.feature.zero_crossing_rate(y)[0]
        if len(zcr) > 0:
            features.zcr_mean = float(np.mean(zcr))
        return features

    # ── Silence / Pauses ───────────────────────────────────────────────

    def _extract_silence(
        self,
        y: np.ndarray,
        sr: int,
        features: AudioFeatures,
        librosa,
    ) -> AudioFeatures:
        """Estimate silence ratio and pause count from non-silent intervals."""
        try:
            # Get non-silent intervals
            intervals = librosa.effects.split(
                y,
                top_db=abs(self._SILENCE_THRESHOLD_DB),
            )

            if len(intervals) == 0 or features.duration_seconds == 0:
                features.silence_ratio = 1.0
                return features

            # Total voiced duration
            voiced_samples = sum(end - start for start, end in intervals)
            total_samples = len(y)
            features.silence_ratio = 1.0 - (voiced_samples / total_samples)

            # Count pauses (gaps between voiced intervals)
            pause_count = 0
            pause_total_samples = 0
            for i in range(1, len(intervals)):
                gap_samples = intervals[i][0] - intervals[i - 1][1]
                gap_duration = gap_samples / sr
                if gap_duration >= self._MIN_PAUSE_DURATION_S:
                    pause_count += 1
                    pause_total_samples += gap_samples

            features.pause_count = pause_count
            features.pause_ratio = pause_total_samples / total_samples

            # Estimate speaking rate from voiced intervals
            if features.duration_seconds > 0:
                voiced_seconds = voiced_samples / sr
                # Heuristic: ~3.5 syllables per second in voiced speech
                features.speaking_rate = (3.5 * voiced_seconds) / features.duration_seconds
        except Exception as exc:
            logger.debug("Silence extraction warning: %s", exc)

        return features

    # ── Voice Stability ────────────────────────────────────────────────

    @staticmethod
    def _compute_voice_stability(features: AudioFeatures) -> AudioFeatures:
        """
        Voice stability = 1 - clamp(pitch_cv, 0, 1).

        High stability (low CV) → AI-like monotone speech.
        Low stability (high CV) → Natural human prosody.
        """
        clamped_cv = min(max(features.pitch_cv, 0.0), 1.0)
        features.voice_stability = 1.0 - clamped_cv
        return features
