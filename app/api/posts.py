from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.post import Post
from app.schemas.post import PostCreate, PostResponse

from app.schemas.matching import ImageRankingResponse
from app.services.matching import rank_images_for_post

router = APIRouter(
    prefix="/posts",
    tags=["posts"],
)


@router.post(
    "",
    response_model=PostResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_post(
    payload: PostCreate,
    db: Session = Depends(get_db),
):
    post = Post(
        title=payload.title,
        content=payload.content,
    )

    db.add(post)
    db.commit()
    db.refresh(post)

    return post


@router.get(
    "",
    response_model=list[PostResponse],
)
def get_posts(
    db: Session = Depends(get_db),
):
    posts = db.scalars(
        select(Post).order_by(Post.id)
    ).all()

    return posts


@router.get(
    "/{post_id}",
    response_model=PostResponse,
)
def get_post(
    post_id: int,
    db: Session = Depends(get_db),
):
    post = db.get(Post, post_id)

    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found.",
        )

    return post


@router.get(
    "/{post_id}/rank-images",
    response_model=ImageRankingResponse,
)
def rank_images(
    post_id: int,
    top_k: int = Query(
        default=10,
        ge=1,
        le=50,
    ),
    db: Session = Depends(get_db),
):
    post = db.get(
        Post,
        post_id,
    )

    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found.",
        )

    try:
        results = rank_images_for_post(
            db=db,
            post=post,
            limit=top_k,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error

    return {
        "post_id": post.id,
        "post_title": post.title,
        "results": results,
    }
