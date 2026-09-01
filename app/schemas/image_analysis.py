from pydantic import BaseModel, Field


class ImageAnalysisResult(BaseModel):
    subject: str = Field(
        min_length=1,
        max_length=255,
        description="The most specific primary subject visible in the image.",
    )

    category: str = Field(
        min_length=1,
        max_length=100,
        description="The broad category of the primary subject.",
    )

    attributes: list[str] = Field(
        min_length=1,
        max_length=8,
        description="Visible characteristics of the primary subject.",
    )

    caption: str = Field(
        min_length=1,
        max_length=500,
        description="One factual sentence describing the image.",
    )

    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence that the primary subject was identified correctly.",
    )
