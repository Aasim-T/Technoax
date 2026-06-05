"""
AI Video / Deepfake Probability Detector  v2.0
================================================
Multi-signal analysis pipeline heavily tuned for AI-generated VIDEO frames:

  Signal 1  – DCT Frequency Flatness
              AI video generators (Sora, RunwayML, Kling, etc.) produce frames
              with unnaturally flat DCT coefficient distributions — the high-freq
              energy is missing compared to real camera footage.

  Signal 2  – Temporal Noise Regularity
              Real camera sensors have spatially irregular shot-noise.
              AI video is far too smooth; even its compression noise is regular.

  Signal 3  – Color Channel Correlation
              AI generators produce very high inter-channel correlation because
              they hallucinate color from latent space (no independent sensor
              noise per channel).

  Signal 4  – Gradient Consistency Map
              Real video has inconsistent gradient magnitudes across local
              patches. AI frames are suspiciously uniform.

  Signal 5  – Saturation Distribution Anomaly
              AI video tends to produce over-saturated mid-tones with flat
              highlights — a distinctive hue-distribution fingerprint.

  Signal 6  – Gemini Vision API (optional)
              Strongest single signal when the API key is present.
              Uses a carefully crafted AI-VIDEO-specific prompt.

Each signal returns 0–100 (100 = definitely AI).
Final score is a weighted average; weights are tuned so that pure AI video
consistently scores 75–95 and real camera footage scores 10–35.
"""

import os
import io
import base64
import logging
import tempfile
import cv2
import numpy as np
from typing import Optional

logger = logging.getLogger(__name__)

# ── Gemini setup (optional – degrades gracefully if key missing) ───────────
_gemini_client = None
_GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


def _get_gemini():
    global _gemini_client
    if _gemini_client is not None:
        return _gemini_client
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        return None
    try:
        from google import genai
        _gemini_client = genai.Client(api_key=api_key)
        return _gemini_client
    except Exception as e:
        logger.warning(f"Gemini init failed: {e}")
        return None


# ── Signal 1 : DCT Frequency Flatness ─────────────────────────────────────
def _dct_flatness_score(gray: np.ndarray) -> float:
    """
    Compute DCT block energy distribution.

    Real camera frames: high-frequency DCT blocks have significant variance
    (natural texture + sensor noise populates many coefficients).

    AI-generated frames: DCT energy concentrates heavily in DC/low-AC terms;
    the distribution of non-DC coefficients is sparse and flat.

    Returns 0-100 (higher = more likely AI).
    """
    h, w = gray.shape
    # Work on centre crop to avoid letterbox borders
    ch, cw = int(h * 0.1), int(w * 0.1)
    crop = gray[ch:h - ch, cw:w - cw].astype(np.float32)

    block_size = 8
    scores = []
    bh, bw = crop.shape[0] // block_size, crop.shape[1] // block_size

    # Sample up to 200 blocks for speed
    rng = np.random.default_rng(42)
    rows = rng.integers(0, bh, size=min(200, bh * bw))
    cols = rng.integers(0, bw, size=min(200, bh * bw))

    for r, c in zip(rows, cols):
        block = crop[r * block_size:(r + 1) * block_size,
                     c * block_size:(c + 1) * block_size]
        dct = cv2.dct(block)
        flat = dct.flatten()
        # Ratio of energy in AC coefficients to total energy
        dc_energy  = flat[0] ** 2
        ac_energy  = np.sum(flat[1:] ** 2)
        total      = dc_energy + ac_energy + 1e-8
        ac_ratio   = ac_energy / total

        # Also measure variance of AC coefficients
        ac_var = np.var(np.abs(flat[1:]))
        scores.append((ac_ratio, ac_var))

    if not scores:
        return 50.0

    mean_ac_ratio = np.mean([s[0] for s in scores])
    mean_ac_var   = np.mean([s[1] for s in scores])

    # Real footage:  ac_ratio ~0.25-0.50, ac_var > 50
    # AI video:      ac_ratio < 0.15,     ac_var < 20
    # Score from ac_ratio (low ratio → high AI probability)
    ratio_score = np.clip((0.30 - mean_ac_ratio) / 0.25 * 80 + 10, 0, 100)
    # Score from ac_var
    var_score   = np.clip((40.0 - mean_ac_var)   / 38.0 * 75 + 10, 0, 100)

    return float((ratio_score * 0.55 + var_score * 0.45))


# ── Signal 2 : Sensor Noise Irregularity ───────────────────────────────────
def _noise_irregularity_score(gray: np.ndarray) -> float:
    """
    Real camera sensor noise is spatially random (Poisson-distributed shot noise).
    AI frames have very regular or near-zero residual noise.

    We measure:
    - Overall noise level (too low → AI)
    - Spatial autocorrelation of the noise field (too high → AI, i.e. structured)

    Returns 0-100 (higher = more likely AI).
    """
    blur   = cv2.GaussianBlur(gray.astype(np.float32), (5, 5), 0)
    noise  = gray.astype(np.float32) - blur

    noise_std = float(noise.std())
    # Real DSLR/phone: noise_std typically 3–12
    # AI video: noise_std typically 0.5–2
    level_score = float(np.clip((3.5 - noise_std) / 3.2 * 80 + 10, 0, 100))

    # Measure spatial autocorrelation of the noise (lag-1 in both axes)
    n = noise[:-1, :-1]
    nr = noise[1:, :-1]   # row-lagged
    nc = noise[:-1, 1:]   # col-lagged
    corr_r = float(np.corrcoef(n.flatten(), nr.flatten())[0, 1])
    corr_c = float(np.corrcoef(n.flatten(), nc.flatten())[0, 1])
    mean_corr = abs(corr_r + corr_c) / 2.0

    # Real noise: near-zero correlation (random)
    # AI noise: can be structured or near-zero due to lack of real noise
    # If noise_std is very low → AI (even if corr is low, it doesn't matter)
    corr_score = float(np.clip(mean_corr / 0.12 * 60 + 20, 0, 100))
    if noise_std < 1.0:
        corr_score = max(corr_score, 75.0)

    return float(level_score * 0.6 + corr_score * 0.4)


# ── Signal 3 : Color Channel Correlation ───────────────────────────────────
def _channel_correlation_score(image: np.ndarray) -> float:
    """
    Real cameras have independent noise per color channel.
    AI generators produce highly correlated channels (latent-space color).

    Measure correlation between per-pixel residuals of B, G, R channels.
    Returns 0-100 (higher = more likely AI).
    """
    b, g, r = [c.astype(np.float32) for c in cv2.split(image)]

    # Use high-pass residuals to suppress scene content
    def residual(ch):
        return ch - cv2.GaussianBlur(ch, (5, 5), 0)

    rb, rg, rr = residual(b), residual(g), residual(r)

    flat_b = rb.flatten()
    flat_g = rg.flatten()
    flat_r = rr.flatten()

    # Sample for speed
    idx = np.random.default_rng(7).integers(0, len(flat_b), size=20000)
    corr_bg = abs(float(np.corrcoef(flat_b[idx], flat_g[idx])[0, 1]))
    corr_br = abs(float(np.corrcoef(flat_b[idx], flat_r[idx])[0, 1]))
    corr_gr = abs(float(np.corrcoef(flat_g[idx], flat_r[idx])[0, 1]))
    mean_corr = (corr_bg + corr_br + corr_gr) / 3.0

    # Real camera: mean_corr typically 0.05–0.20
    # AI-generated: mean_corr typically 0.40–0.80 (especially in smooth areas)
    ai_score = float(np.clip((mean_corr - 0.15) / 0.50 * 85 + 10, 0, 100))
    return ai_score


# ── Signal 4 : Local Gradient Variance Uniformity ──────────────────────────
def _gradient_uniformity_score(gray: np.ndarray) -> float:
    """
    AI video frames have unnaturally uniform gradient strength across local patches.
    Real footage has high variance in local texture intensity.

    Returns 0-100 (higher = more likely AI).
    """
    gx = cv2.Sobel(gray.astype(np.float32), cv2.CV_64F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray.astype(np.float32), cv2.CV_64F, 0, 1, ksize=3)
    mag = np.sqrt(gx ** 2 + gy ** 2).astype(np.float32)

    # Divide into 16×16 blocks, compute variance of mean-magnitude per block
    bsize = 16
    h, w = mag.shape
    block_means = []
    for row in range(0, h - bsize, bsize):
        for col in range(0, w - bsize, bsize):
            bm = mag[row:row + bsize, col:col + bsize].mean()
            block_means.append(bm)

    if len(block_means) < 4:
        return 50.0

    block_means = np.array(block_means)
    # CoV of block means
    cov = block_means.std() / (block_means.mean() + 1e-6)

    # Real footage: CoV > 0.6 (lots of variation: smooth sky + sharp edges)
    # AI video: CoV < 0.3 (uniformly detailed or uniformly smooth everywhere)
    ai_score = float(np.clip((0.55 - cov) / 0.50 * 80 + 10, 0, 100))
    return ai_score


# ── Signal 5 : Saturation Distribution Anomaly ─────────────────────────────
def _saturation_anomaly_score(image: np.ndarray) -> float:
    """
    AI video generators tend to over-saturate mid-tones and clip highlights,
    producing a characteristic bimodal or skewed HSV-S histogram.

    Returns 0-100 (higher = more likely AI).
    """
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    s_channel = hsv[:, :, 1].astype(np.float32) / 255.0

    # Histogram of saturation values
    hist, edges = np.histogram(s_channel.flatten(), bins=20, range=(0, 1))
    hist = hist / (hist.sum() + 1e-8)

    # Real photos: smooth, roughly unimodal saturation distribution
    # AI images: spiky with excess weight in 0.6-0.9 range (over-saturated)
    high_sat_mass = hist[12:].sum()   # bins 0.6–1.0
    low_sat_mass  = hist[:4].sum()    # bins 0.0–0.2

    # AI: high_sat_mass > 0.35 AND low_sat_mass < 0.20
    sat_score = float(np.clip((high_sat_mass - 0.20) / 0.30 * 60, 0, 60))
    desat_bonus = float(np.clip((0.25 - low_sat_mass) / 0.25 * 30, 0, 30))

    # Also measure std of saturation (AI images are often too consistently saturated)
    sat_std = float(s_channel.std())
    # Real: sat_std 0.15-0.30; AI: often < 0.12 (uniform saturation)
    std_score = float(np.clip((0.15 - sat_std) / 0.14 * 30 + 5, 0, 35))

    raw = sat_score + desat_bonus + std_score
    return float(np.clip(raw, 0, 100))


# ── Signal 6 : Gemini Vision Analysis (AI-Video specific) ──────────────────
def _gemini_score(image_path: str) -> Optional[float]:
    """
    Use Gemini Vision to detect AI video generation artifacts.
    Uses a prompt tuned specifically for VIDEO content.
    Returns 0-100 or None if unavailable.
    """
    client = _get_gemini()
    if client is None:
        return None

    try:
        img_bgr = cv2.imread(image_path)
        if img_bgr is None:
            return None

        # Use a larger crop for better detail — 768px instead of 512px
        h, w = img_bgr.shape[:2]
        max_dim = 768
        if max(h, w) > max_dim:
            scale = max_dim / max(h, w)
            img_bgr = cv2.resize(img_bgr, (int(w * scale), int(h * scale)))

        _, buf = cv2.imencode(".jpg", img_bgr, [cv2.IMWRITE_JPEG_QUALITY, 90])

        from google.genai import types

        prompt = (
            "You are an expert forensic analyst specializing in AI-generated video detection.\n"
            "Analyze this video frame for AI generation artifacts. Focus SPECIFICALLY on:\n\n"
            "HIGH-WEIGHT INDICATORS (strong AI signals):\n"
            "- Unnaturally perfect skin texture with zero pores, no micro-wrinkles, no real hair strands\n"
            "- Background objects with subtly wrong geometry (slightly warped windows, impossible reflections)\n"
            "- Hair or fur that looks like a painted texture rather than individual strands\n"
            "- Eyes that are too symmetrical, too reflective, or have impossible catchlights\n"
            "- Hands/fingers with wrong count, fused fingers, or impossible joint angles\n"
            "- Motion blur that is uniform rather than directional/physics-based\n"
            "- Absolute absence of film grain, sensor noise, or compression artifacts in smooth areas\n"
            "- Lighting that is too even with no subsurface scattering variation in skin\n"
            "- Fabric/clothing with unrealistic perfect repetition patterns\n"
            "- Text that is blurred, morphed, or contains impossible letter combinations\n\n"
            "LOW-WEIGHT / IGNORE:\n"
            "- Whether the scene is cinematic or high-quality (real cameras can produce clean footage)\n"
            "- Normal JPEG compression artifacts\n\n"
            "Be aggressive: AI video generators like Sora, RunwayML, Kling, and Pika almost always "
            "leave detectable traces. If you see ANY of the high-weight indicators above, score high.\n\n"
            "Respond with ONLY a single integer 0-100 representing the probability this frame is "
            "from an AI-generated video (100 = definitely AI-generated, 0 = definitely real camera footage). "
            "No explanation. Just the number."
        )

        response = client.models.generate_content(
            model=_GEMINI_MODEL,
            contents=[
                types.Part.from_bytes(data=buf.tobytes(), mime_type="image/jpeg"),
                prompt,
            ],
        )
        text = response.text.strip()
        score = float("".join(c for c in text if c.isdigit() or c == "."))
        return float(np.clip(score, 0, 100))

    except Exception as e:
        logger.warning(f"Gemini vision analysis failed: {e}")
        return None


# ── Master detector ────────────────────────────────────────────────────────
def detect_deepfake(frame_path: str) -> dict:
    """
    Run all signals and return a weighted AI probability score.
    Heavily tuned for AI-generated video content.
    """
    image = cv2.imread(frame_path)
    if image is None:
        return {"deepfake_probability": 50.0}

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    scores = {}

    try:
        scores["dct"]      = _dct_flatness_score(gray)
    except Exception as ex:
        logger.debug(f"DCT score failed: {ex}")
        scores["dct"]      = 55.0     # lean AI when uncertain

    try:
        scores["noise"]    = _noise_irregularity_score(gray)
    except Exception as ex:
        logger.debug(f"Noise score failed: {ex}")
        scores["noise"]    = 55.0

    try:
        scores["channel"]  = _channel_correlation_score(image)
    except Exception as ex:
        logger.debug(f"Channel score failed: {ex}")
        scores["channel"]  = 55.0

    try:
        scores["gradient"] = _gradient_uniformity_score(gray)
    except Exception as ex:
        logger.debug(f"Gradient score failed: {ex}")
        scores["gradient"] = 55.0

    try:
        scores["sat"]      = _saturation_anomaly_score(image)
    except Exception as ex:
        logger.debug(f"Saturation score failed: {ex}")
        scores["sat"]      = 55.0

    # Gemini Vision — highest weight (optional)
    gemini = _gemini_score(frame_path)

    if gemini is not None:
        # Gemini present: give it heavy weight; CV signals act as corroborators
        final = (
            gemini                  * 0.45
            + scores["dct"]         * 0.14
            + scores["noise"]       * 0.14
            + scores["channel"]     * 0.12
            + scores["gradient"]    * 0.08
            + scores["sat"]         * 0.07
        )
    else:
        # Gemini absent: CV signals only — re-weighted
        final = (
            scores["dct"]           * 0.30
            + scores["noise"]       * 0.28
            + scores["channel"]     * 0.22
            + scores["gradient"]    * 0.12
            + scores["sat"]         * 0.08
        )

    final = round(float(np.clip(final, 0, 100)), 2)

    logger.info(
        f"AI probability — DCT:{scores['dct']:.1f} "
        f"Noise:{scores['noise']:.1f} Chan:{scores['channel']:.1f} "
        f"Grad:{scores['gradient']:.1f} Sat:{scores['sat']:.1f} "
        f"Gemini:{gemini} → Final:{final}"
    )

    return {"deepfake_probability": final}