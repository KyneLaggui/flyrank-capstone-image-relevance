from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.image import Image

from app.schemas.image import (
    ImageAnalysisResponse,
    ImageCreate,
    ImageResponse,
)
from app.services.image_processing import process_image
from google.genai.errors import ClientError


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


@router.post(
    "/{image_id}/analyze",
    response_model=ImageAnalysisResponse,
)
def analyze_image(
    image_id: int,
    db: Session = Depends(get_db),
):
    image = db.get(Image, image_id)

    if image is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found.",
        )

    try:
        metadata = process_image(
            db=db,
            image=image,
        )

    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The image file could not be found.",
        )

    except ClientError as error:
        if error.code == 429:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Gemini rate limit exceeded. Try again later.",
            ) from error

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Gemini API request failed.",
        ) from error

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Image analysis failed.",
        )

    db.refresh(image)

    return {
        "image_id": image.id,
        "processing_status": image.processing_status,
        "metadata": metadata,
    }


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
