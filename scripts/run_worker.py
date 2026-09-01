import time
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models.image import Image
from app.models.job import ProcessingJob
from app.models.post import Post
from app.services.embedding_processing import (
    embed_image,
    embed_post,
)
from app.services.image_processing import process_image


POLL_INTERVAL_SECONDS = 2
MAX_RETRIES = 3


def get_next_job(
    db: Session,
) -> ProcessingJob | None:
    return db.scalar(
        select(ProcessingJob)
        .where(
            ProcessingJob.status == "queued",
            ProcessingJob.job_type.in_(
                [
                    "image_processing",
                    "embedding_generation",
                ]
            ),
        )
        .order_by(ProcessingJob.id)
        .limit(1)
    )


def finish_job(
    db: Session,
    job_id: int,
) -> None:
    job = db.get(
        ProcessingJob,
        job_id,
    )

    if job is None:
        raise RuntimeError(
            "Processing job no longer exists."
        )

    if job.failed_items > 0:
        job.status = "completed_with_errors"
        job.error_message = (
            f"{job.failed_items} item(s) "
            f"failed after retries."
        )
    else:
        job.status = "completed"
        job.error_message = None

    job.completed_at = datetime.now(
        timezone.utc
    )

    db.commit()

    print()
    print(
        f"Job {job.id} finished: "
        f"{job.status}"
    )


def process_image_job(
    db: Session,
    job: ProcessingJob,
) -> None:
    job_id = job.id

    image_ids = list(
        db.scalars(
            select(Image.id)
            .where(
                Image.processing_status
                == "pending"
            )
            .order_by(Image.id)
        )
    )

    job.status = "processing"
    job.started_at = datetime.now(
        timezone.utc
    )
    job.total_items = len(image_ids)
    job.processed_items = 0
    job.failed_items = 0
    job.error_message = None

    db.commit()

    for image_id in image_ids:
        success = False
        final_error = None

        for attempt in range(
            1,
            MAX_RETRIES + 1,
        ):
            image = db.get(
                Image,
                image_id,
            )

            if image is None:
                final_error = (
                    "Image record not found."
                )
                break

            print(
                f"[Job {job_id}] "
                f"Processing {image.filename} "
                f"({attempt}/{MAX_RETRIES})"
            )

            try:
                process_image(
                    db=db,
                    image=image,
                )

                success = True

                print(
                    f"[Job {job_id}] "
                    f"Completed {image.filename}"
                )

                break

            except Exception as error:
                db.rollback()

                final_error = str(error)

                print(
                    f"[Job {job_id}] "
                    f"Failed {image.filename}: "
                    f"{error}"
                )

                if attempt < MAX_RETRIES:
                    time.sleep(
                        2 ** attempt
                    )

        job = db.get(
            ProcessingJob,
            job_id,
        )

        if job is None:
            raise RuntimeError(
                "Processing job disappeared."
            )

        if success:
            job.processed_items += 1
        else:
            job.failed_items += 1

        db.commit()

        print(
            f"Progress: "
            f"{job.processed_items + job.failed_items}"
            f"/{job.total_items}"
        )

    finish_job(
        db=db,
        job_id=job_id,
    )


def process_embedding_job(
    db: Session,
    job: ProcessingJob,
) -> None:
    job_id = job.id

    image_ids = list(
        db.scalars(
            select(Image.id)
            .where(
                Image.processing_status
                == "completed"
            )
            .order_by(Image.id)
        )
    )

    post_ids = list(
        db.scalars(
            select(Post.id)
            .order_by(Post.id)
        )
    )

    resources = [
        ("image", resource_id)
        for resource_id in image_ids
    ]

    resources.extend(
        [
            ("post", resource_id)
            for resource_id in post_ids
        ]
    )

    job.status = "processing"
    job.started_at = datetime.now(
        timezone.utc
    )
    job.total_items = len(resources)
    job.processed_items = 0
    job.failed_items = 0
    job.error_message = None

    db.commit()

    print(
        f"Embedding {len(resources)} resources."
    )

    for resource_type, resource_id in resources:
        success = False
        final_error = None

        for attempt in range(
            1,
            MAX_RETRIES + 1,
        ):
            print(
                f"[Job {job_id}] "
                f"Embedding "
                f"{resource_type} "
                f"{resource_id} "
                f"({attempt}/{MAX_RETRIES})"
            )

            try:
                if resource_type == "image":
                    image = db.get(
                        Image,
                        resource_id,
                    )

                    if image is None:
                        raise RuntimeError(
                            "Image not found."
                        )

                    embed_image(
                        db=db,
                        image=image,
                    )

                elif resource_type == "post":
                    post = db.get(
                        Post,
                        resource_id,
                    )

                    if post is None:
                        raise RuntimeError(
                            "Post not found."
                        )

                    embed_post(
                        db=db,
                        post=post,
                    )

                success = True

                print(
                    f"[Job {job_id}] "
                    f"Completed "
                    f"{resource_type} "
                    f"{resource_id}"
                )

                break

            except Exception as error:
                db.rollback()

                final_error = str(error)

                print(
                    f"[Job {job_id}] "
                    f"Failed "
                    f"{resource_type} "
                    f"{resource_id}: "
                    f"{error}"
                )

                if attempt < MAX_RETRIES:
                    wait_seconds = (
                        2 ** attempt
                    )

                    print(
                        f"Retrying in "
                        f"{wait_seconds} seconds..."
                    )

                    time.sleep(
                        wait_seconds
                    )

        job = db.get(
            ProcessingJob,
            job_id,
        )

        if job is None:
            raise RuntimeError(
                "Processing job disappeared."
            )

        if success:
            job.processed_items += 1

        else:
            job.failed_items += 1

            if final_error:
                print(
                    f"Final failure: "
                    f"{final_error}"
                )

        db.commit()

        print(
            f"Progress: "
            f"{job.processed_items + job.failed_items}"
            f"/{job.total_items}"
        )

    finish_job(
        db=db,
        job_id=job_id,
    )


def process_job(
    db: Session,
    job: ProcessingJob,
) -> None:
    print()
    print(
        f"Starting job {job.id}: "
        f"{job.job_type}"
    )

    if job.job_type == "image_processing":
        process_image_job(
            db=db,
            job=job,
        )

    elif job.job_type == "embedding_generation":
        process_embedding_job(
            db=db,
            job=job,
        )

    else:
        raise ValueError(
            f"Unsupported job type: "
            f"{job.job_type}"
        )


def main() -> None:
    print(
        "Background worker started."
    )
    print(
        "Waiting for jobs..."
    )

    while True:
        db = SessionLocal()

        try:
            job = get_next_job(db)

            if job is None:
                time.sleep(
                    POLL_INTERVAL_SECONDS
                )
                continue

            process_job(
                db=db,
                job=job,
            )

        except KeyboardInterrupt:
            print()
            print(
                "Worker stopped."
            )
            break

        except Exception as error:
            db.rollback()

            print(
                f"Worker error: {error}"
            )

            time.sleep(
                POLL_INTERVAL_SECONDS
            )

        finally:
            db.close()


if __name__ == "__main__":
    main()
