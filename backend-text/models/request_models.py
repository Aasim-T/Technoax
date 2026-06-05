"""Request body models for Technoax API."""

from pydantic import BaseModel, Field


class AnalyzeTextRequest(BaseModel):
    """Payload for text trust analysis."""

    text: str = Field(
        ...,
        min_length=1,
        max_length=50_000,
        description="Text content to analyze for manipulation patterns",
        examples=[
            "URGENT: Act now before disaster strikes! You won't believe this shocking secret."
        ],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "text": (
                        "WARNING: Immediate danger ahead. Share now before it's too late! "
                        "This unbelievable hidden truth will shock you."
                    )
                }
            ]
        }
    }
