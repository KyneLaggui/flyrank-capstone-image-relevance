from pydantic import BaseModel


class RankedImageResponse(BaseModel):
    image_id: int
    filename: str
    subject: str | None
    category: str | None
    similarity: float


class ImageRankingResponse(BaseModel):
    post_id: int
    post_title: str
    results: list[RankedImageResponse]
