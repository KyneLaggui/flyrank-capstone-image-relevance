from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ImageCreate(BaseModel):
    filename: str = Field(
        min_length=1,
        max_length=255,
    )

    file_path: str = Field(
        min_length=1,
        max_length=500,
    )


class ImageResponse(BaseModel):
    id: int
    filename: str
    file_path: str
    processing_status: str
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class ImageMetadataResponse(BaseModel):
    subject: str
    category: str
    attributes: list[str]
    caption: str
    confidence: float
    flagged: bool

    model_config = ConfigDict(
        from_attributes=True,
    )


class ImageAnalysisResponse(BaseModel):
    image_id: int
    processing_status: str
    metadata: ImageMetadataResponse
