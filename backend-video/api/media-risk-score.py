from fastapi import APIRouter

from services.multi_frame_analyzer import (
    analyze_multiple_frames
)

router = APIRouter()

FRAME_DIR = "frames/extracted"

@router.get("/media-risk-score")
def media_risk_score():

    result = analyze_multiple_frames(
        FRAME_DIR
    )

    return result