from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def root():
    return {"status": "API Running"}

@router.get("/health")
def health_check():
    return {"status": "ok", "service": "Technoax Video Analysis API"}