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
    active_job = db.scalar(
        select(ProcessingJob).where(
            ProcessingJob.job_type == "image_processing",
            ProcessingJob.status.in_(
                ["queued", "processing"]
            ),
        )
    )

    if active_job is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An image processing job is already active.",
        )

    pending_count = db.scalar(
        select(func.count(Image.id)).where(
            Image.processing_status == "pending"
        )
    )

    if not pending_count:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="There are no pending images to process.",
        )

    job = ProcessingJob(
        job_type="image_processing",
        status="queued",
        total_items=pending_count,
        processed_items=0,
        failed_items=0,
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
