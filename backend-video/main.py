from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from api.analyze_video import router as analyze_router
from api.frame_analysis import router as frame_router
from api.media_risk_score import router as risk_router
from api.health import router as health_router

app = FastAPI(
    title="Technoax Media Intelligence API"
)

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyze_router)
app.include_router(frame_router)
app.include_router(risk_router)
app.include_router(health_router)