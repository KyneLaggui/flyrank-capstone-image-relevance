from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.image import Image
from app.models.post import Post
from app.services.matching import (
    rank_images_for_post,
)
from app.services.mismatch_guard import (
    evaluate_candidate,
)


@dataclass
class RecommendationCandidate:
    image_id: int
    filename: str

    subject: str | None
    category: str | None

    similarity: float
    confidence: float | None

    accepted: bool
    reason: str


@dataclass
class RecommendationResult:
    match_found: bool
    message: str

    recommendation: (
        RecommendationCandidate | None
    )

    reasons: list[str]

    candidates: list[
        RecommendationCandidate
    ]


def recommend_images_for_post(
    db: Session,
    post: Post,
    response_limit: int = 10,
) -> RecommendationResult:
    ranked_images = rank_images_for_post(
        db=db,
        post=post,
        limit=1000,
    )

    evaluated_candidates: list[
        RecommendationCandidate
    ] = []

    best_match: (
        RecommendationCandidate | None
    ) = None

    for ranked_image in ranked_images:
        image = db.get(
            Image,
            ranked_image.image_id,
        )

        if image is None:
            continue

        decision = evaluate_candidate(
            post=post,
            image=image,
            similarity=ranked_image.similarity,
        )

        metadata = image.metadata_record

        candidate = RecommendationCandidate(
            image_id=image.id,
            filename=image.filename,
            subject=(
                metadata.subject
                if metadata
                else None
            ),
            category=(
                metadata.category
                if metadata
                else None
            ),
            similarity=ranked_image.similarity,
            confidence=(
                metadata.confidence
                if metadata
                else None
            ),
            accepted=decision.accepted,
            reason=decision.reason,
        )

        evaluated_candidates.append(
            candidate
        )

        if (
            best_match is None
            and decision.accepted
        ):
            best_match = candidate

    visible_candidates = (
        evaluated_candidates[
            :response_limit
        ]
    )

    if best_match is not None:
        return RecommendationResult(
            match_found=True,
            message="Confident match found.",
            recommendation=best_match,
            reasons=[],
            candidates=visible_candidates,
        )

    unique_reasons: list[str] = []

    for candidate in evaluated_candidates:
        if candidate.reason not in unique_reasons:
            unique_reasons.append(
                candidate.reason
            )

        if len(unique_reasons) >= 5:
            break

    return RecommendationResult(
        match_found=False,
        message="No confident match.",
        recommendation=None,
        reasons=unique_reasons,
        candidates=visible_candidates,
    )
