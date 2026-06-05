from pydantic import BaseModel

class VideoRequest(BaseModel):

    filename: str