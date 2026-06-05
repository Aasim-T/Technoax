import os

from services.face_detector import detect_faces
from services.artifact_detector import detect_blur
from services.visual_analyzer import calculate_brightness
from services.deepfake_detector import detect_deepfake

def analyze_multiple_frames(frame_dir):

    frames = sorted(os.listdir(frame_dir))

    selected_frames = frames[::10]

    total_faces = 0
    total_blur = 0
    total_brightness = 0
    total_deepfake = 0

    analyzed = 0

    for frame in selected_frames:

        frame_path = os.path.join(
            frame_dir,
            frame
        )

        total_faces += detect_faces(frame_path)

        total_blur += detect_blur(frame_path)

        total_brightness += calculate_brightness(
            frame_path
        )

        total_deepfake += detect_deepfake(
            frame_path
        )["deepfake_probability"]

        analyzed += 1

    return {
        "frames_checked": analyzed,
        "avg_faces": round(total_faces / analyzed, 2),
        "avg_blur": round(total_blur / analyzed, 2),
        "avg_brightness": round(total_brightness / analyzed, 2),
        "avg_deepfake": round(total_deepfake / analyzed, 2)
    }