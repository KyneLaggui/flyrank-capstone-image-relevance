from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.post import Post
from app.models.suggestion import (
    Suggestion,
    SuggestionReview,
)
from app.services.recommendation import (
    recommend_images_for_post,
)


def create_suggestion_for_post(
    db: Session,
    post: Post,
) -> Suggestion:
    result = recommend_images_for_post(
        db=db,
        post=post,
        response_limit=10,
    )

    candidate = result.recommendation

    if (
        not result.match_found
        or candidate is None
    ):
        raise ValueError(
            "No confident match is available "
            "for this post."
        )

    existing = db.scalar(
        select(Suggestion).where(
            Suggestion.post_id == post.id,
            Suggestion.image_id
            == candidate.image_id,
        )
    )

    if existing is not None:
        if existing.status == "pending":
            existing.similarity = (
                candidate.similarity
            )
            existing.confidence = (
                candidate.confidence
            )
            existing.guard_accepted = (
                candidate.accepted
            )
            existing.guard_reason = (
                candidate.reason
            )

            db.commit()
            db.refresh(existing)

        return existing

    suggestion = Suggestion(
        post_id=post.id,
        image_id=candidate.image_id,
        similarity=candidate.similarity,
        confidence=candidate.confidence,
        guard_accepted=candidate.accepted,
        guard_reason=candidate.reason,
        status="pending",
    )

    db.add(suggestion)
    db.commit()
    db.refresh(suggestion)

    return suggestion


def get_suggestion_review(
    db: Session,
    suggestion_id: int,
) -> SuggestionReview | None:
    return db.scalar(
        select(SuggestionReview).where(
            SuggestionReview.suggestion_id
            == suggestion_id
        )
    )


def review_suggestion(
    db: Session,
    suggestion: Suggestion,
    decision: str,
    note: str | None,
) -> SuggestionReview:
    if suggestion.status != "pending":
        raise ValueError(
            "Suggestion has already been reviewed."
        )

    if decision not in {
        "approved",
        "rejected",
    }:
        raise ValueError(
            "Invalid review decision."
        )

    if (
        decision == "approved"
        and not suggestion.guard_accepted
    ):
        raise ValueError(
            "A suggestion rejected by the "
            "mismatch guard cannot be approved."
        )

    review = SuggestionReview(
        suggestion_id=suggestion.id,
        decision=decision,
        note=note,
    )

    suggestion.status = decision

    db.add(review)
    db.commit()

    db.refresh(suggestion)
    db.refresh(review)

    return review
