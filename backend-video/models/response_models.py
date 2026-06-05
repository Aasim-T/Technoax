from pydantic import BaseModel

class VideoResponse(BaseModel):

    filename: str
    risk_score: int
    status: str