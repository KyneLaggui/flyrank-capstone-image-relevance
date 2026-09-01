from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.image import Image
from app.models.job import ProcessingJob
from app.schemas.job import ProcessingJobResponse


router = APIRouter(
    prefix="/jobs",
    tags=["jobs"],
)


@router.post(
    "/image-processing",
    response_model=ProcessingJobResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_image_processing_job(
    db: Session = Depends(get_db),
):
    pending_count = db.scalar(
        select(func.count())
        .select_from(Image)
        .where(Image.processing_status == "pending")
    )

    if pending_count == 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="There are no pending images to process.",
        )

    job = ProcessingJob(
        job_type="image_processing",
        status="queued",
        total_items=pending_count,
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    return job


@router.get(
    "/{job_id}",
    response_model=ProcessingJobResponse,
)
def get_job(
    job_id: int,
    db: Session = Depends(get_db),
):
    job = db.get(ProcessingJob, job_id)

    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found.",
        )

    return job
