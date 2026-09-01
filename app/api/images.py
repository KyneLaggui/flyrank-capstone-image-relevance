from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.image import Image
from app.schemas.image import ImageCreate, ImageResponse


router = APIRouter(
    prefix="/images",
    tags=["images"],
)


@router.post(
    "",
    response_model=ImageResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_image(
    payload: ImageCreate,
    db: Session = Depends(get_db),
):
    existing_image = db.scalar(
        select(Image).where(
            Image.filename == payload.filename
        )
    )

    if existing_image:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An image with this filename already exists.",
        )

    image = Image(
        filename=payload.filename,
        file_path=payload.file_path,
    )

    db.add(image)
    db.commit()
    db.refresh(image)

    return image


@router.get(
    "",
    response_model=list[ImageResponse],
)
def get_images(
    db: Session = Depends(get_db),
):
    images = db.scalars(
        select(Image).order_by(Image.id)
    ).all()

    return images


@router.get(
    "/{image_id}",
    response_model=ImageResponse,
)
def get_image(
    image_id: int,
    db: Session = Depends(get_db),
):
    image = db.get(Image, image_id)

    if image is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found.",
        )

    return image
