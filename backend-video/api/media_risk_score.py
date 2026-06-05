from fastapi import APIRouter

router = APIRouter()

@router.get("/media-risk-score")
def media_risk_score():

    return {
        "risk_score": 72,
        "risk_level": "Medium"
    }