import os
import numpy as np

from services.face_detector import detect_faces
from services.artifact_detector import detect_blur
from services.visual_analyzer import calculate_brightness
from services.deepfake_detector import detect_deepfake


def analyze_multiple_frames(frame_dir, max_frames: int = 12):
    """
    Analyze a representative sample of frames from the extracted directory.

    Strategy:
    - Sample evenly across the video (not every 10th, which can skip most frames
      in a short video or miss key sections of a long one).
    - Cap at max_frames (default 12) to balance accuracy with speed.
    - For deepfake scoring, use ALL sampled frames; for slower signals (faces,
      blur, brightness) the same sample is used to keep runtimes sane.
    """
    frames = sorted(os.listdir(frame_dir))
    if not frames:
        return {
            "frames_checked": 0,
            "avg_faces": 0,
            "avg_blur": 0.0,
            "avg_brightness": 0.0,
            "avg_deepfake": 50.0,
        }

    # Even stride sampling — pick up to max_frames spread across the whole video
    n = len(frames)
    if n <= max_frames:
        selected_frames = frames
    else:
        indices = np.linspace(0, n - 1, max_frames, dtype=int)
        selected_frames = [frames[i] for i in indices]

    total_faces = 0
    total_blur = 0
    total_brightness = 0
    total_deepfake = 0
    analyzed = 0

    for frame in selected_frames:
        frame_path = os.path.join(frame_dir, frame)

        try:
            total_faces      += detect_faces(frame_path)
            total_blur       += detect_blur(frame_path)
            total_brightness += calculate_brightness(frame_path)
            total_deepfake   += detect_deepfake(frame_path)["deepfake_probability"]
            analyzed         += 1
        except Exception:
            # Skip corrupt frames but don't abort the whole analysis
            continue

    if analyzed == 0:
        return {
            "frames_checked": 0,
            "avg_faces": 0,
            "avg_blur": 0.0,
            "avg_brightness": 0.0,
            "avg_deepfake": 50.0,
        }

    return {
        "frames_checked": analyzed,
        "avg_faces":      round(total_faces      / analyzed, 2),
        "avg_blur":       round(total_blur        / analyzed, 2),
        "avg_brightness": round(total_brightness  / analyzed, 2),
        "avg_deepfake":   round(total_deepfake    / analyzed, 2),
    }