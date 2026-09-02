from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SuggestionCreate(BaseModel):
    post_id: int = Field(gt=0)


class SuggestionReviewCreate(BaseModel):
    note: str | None = Field(
        default=None,
        max_length=500,
    )


class SuggestionReviewResponse(BaseModel):
    id: int
    suggestion_id: int
    decision: str
    note: str | None
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class SuggestionResponse(BaseModel):
    id: int
    post_id: int
    image_id: int

    similarity: float
    confidence: float | None

    guard_accepted: bool
    guard_reason: str

    status: str

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class SuggestionDetailResponse(
    SuggestionResponse
):
    review: SuggestionReviewResponse | None
