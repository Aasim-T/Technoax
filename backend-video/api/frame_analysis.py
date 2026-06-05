from fastapi import APIRouter
import os
from services.deepfake_detector import detect_deepfake
from services.face_detector import detect_faces
from services.artifact_detector import detect_blur
from services.visual_analyzer import calculate_brightness
from services.explanation_engine import generate_explanation
from services.risk_calculator import calculate_risk_score

router = APIRouter()

FRAME_DIR = "frames/extracted"

@router.get("/frame-analysis")
def frame_analysis():

    if not os.path.exists(FRAME_DIR):

        return {
            "error":
            "No frames found"
        }

    frames = os.listdir(FRAME_DIR)

    if len(frames) == 0:

        return {
            "error":
            "No extracted frames"
        }

    frame_file = os.path.join(
        FRAME_DIR,
        frames[0]
    )

    face_count = detect_faces(
        frame_file
    )

    blur_score = detect_blur(
        frame_file
    )

    brightness = calculate_brightness(
        frame_file
    )

    deepfake = detect_deepfake(
    frame_file
    )

    risk = calculate_risk_score(
    face_count,
    blur_score,
    brightness,
    deepfake["deepfake_probability"]
    )
    explanation = generate_explanation(
    face_count,
    blur_score,
    brightness,
    deepfake["deepfake_probability"],
    risk["risk_level"]
)

    return {
    "frame": frames[0],
    "faces_detected": face_count,
    "blur_score": round(
        blur_score,
        2
    ),
    "brightness": round(
        brightness,
        2
    ),
    "deepfake_probability":
        deepfake["deepfake_probability"],

    "risk_score":
        risk["risk_score"],

    "risk_level":
        risk["risk_level"],

    "explanation": explanation
}