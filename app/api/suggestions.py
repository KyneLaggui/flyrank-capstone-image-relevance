from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.post import Post
from app.models.suggestion import Suggestion
from app.schemas.suggestion import (
    SuggestionCreate,
    SuggestionDetailResponse,
    SuggestionResponse,
    SuggestionReviewCreate,
)
from app.services.suggestion import (
    create_suggestion_for_post,
    get_suggestion_review,
    review_suggestion,
)


router = APIRouter(
    prefix="/suggestions",
    tags=["suggestions"],
)


def build_suggestion_detail(
    db: Session,
    suggestion: Suggestion,
):
    review = get_suggestion_review(
        db=db,
        suggestion_id=suggestion.id,
    )

    return {
        "id": suggestion.id,
        "post_id": suggestion.post_id,
        "image_id": suggestion.image_id,
        "similarity": suggestion.similarity,
        "confidence": suggestion.confidence,
        "guard_accepted": (
            suggestion.guard_accepted
        ),
        "guard_reason": (
            suggestion.guard_reason
        ),
        "status": suggestion.status,
        "created_at": suggestion.created_at,
        "updated_at": suggestion.updated_at,
        "review": review,
    }


@router.post(
    "",
    response_model=SuggestionDetailResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_suggestion(
    payload: SuggestionCreate,
    db: Session = Depends(get_db),
):
    post = db.get(
        Post,
        payload.post_id,
    )

    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found.",
        )

    try:
        suggestion = (
            create_suggestion_for_post(
                db=db,
                post=post,
            )
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error

    return build_suggestion_detail(
        db=db,
        suggestion=suggestion,
    )


@router.get(
    "",
    response_model=list[SuggestionResponse],
)
def get_suggestions(
    db: Session = Depends(get_db),
):
    return list(
        db.scalars(
            select(Suggestion)
            .order_by(Suggestion.id)
        )
    )


@router.get(
    "/{suggestion_id}",
    response_model=SuggestionDetailResponse,
)
def get_suggestion(
    suggestion_id: int,
    db: Session = Depends(get_db),
):
    suggestion = db.get(
        Suggestion,
        suggestion_id,
    )

    if suggestion is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Suggestion not found.",
        )

    return build_suggestion_detail(
        db=db,
        suggestion=suggestion,
    )


@router.post(
    "/{suggestion_id}/approve",
    response_model=SuggestionDetailResponse,
)
def approve_suggestion(
    suggestion_id: int,
    payload: SuggestionReviewCreate,
    db: Session = Depends(get_db),
):
    suggestion = db.get(
        Suggestion,
        suggestion_id,
    )

    if suggestion is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Suggestion not found.",
        )

    try:
        review_suggestion(
            db=db,
            suggestion=suggestion,
            decision="approved",
            note=payload.note,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error

    return build_suggestion_detail(
        db=db,
        suggestion=suggestion,
    )


@router.post(
    "/{suggestion_id}/reject",
    response_model=SuggestionDetailResponse,
)
def reject_suggestion(
    suggestion_id: int,
    payload: SuggestionReviewCreate,
    db: Session = Depends(get_db),
):
    suggestion = db.get(
        Suggestion,
        suggestion_id,
    )

    if suggestion is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Suggestion not found.",
        )

    try:
        review_suggestion(
            db=db,
            suggestion=suggestion,
            decision="rejected",
            note=payload.note,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error

    return build_suggestion_detail(
        db=db,
        suggestion=suggestion,
    )
