from pydantic import BaseModel


class GuardCheckResponse(BaseModel):
    post_id: int
    image_id: int
    filename: str

    similarity: float

    accepted: bool
    reason: str

    post_subject: str | None
    image_subject: str | None

    confidence: float | None
