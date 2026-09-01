from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PostCreate(BaseModel):
    title: str = Field(
        min_length=1,
        max_length=255,
    )

    content: str = Field(
        min_length=1,
    )


class PostResponse(BaseModel):
    id: int
    title: str
    content: str
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )
