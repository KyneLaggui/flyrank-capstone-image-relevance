from pydantic import BaseModel


class RecommendationCandidateResponse(BaseModel):
    image_id: int
    filename: str

    subject: str | None
    category: str | None

    similarity: float
    confidence: float | None

    accepted: bool
    reason: str


class PostImageRecommendationResponse(BaseModel):
    post_id: int
    post_title: str

    match_found: bool
    message: str

    recommendation: (
        RecommendationCandidateResponse
        | None
    )

    reasons: list[str]

    candidates: list[
        RecommendationCandidateResponse
    ]
