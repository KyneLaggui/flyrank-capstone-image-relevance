import time
from datetime import datetime, timezone

from sqlalchemy import select

from app.db import SessionLocal
from app.models.image import Image
from app.models.job import ProcessingJob
from app.services.image_processing import process_image


POLL_INTERVAL_SECONDS = 2
MAX_RETRIES = 3


def get_next_job(
    db,
) -> ProcessingJob | None:
    return db.scalar(
        select(ProcessingJob)
        .where(
            ProcessingJob.job_type == "image_processing",
            ProcessingJob.status == "queued",
        )
        .order_by(ProcessingJob.id)
        .limit(1)
    )


def process_job(
    db,
    job: ProcessingJob,
) -> None:
    job_id = job.id

    print(f"Starting job {job_id}")

    job.status = "processing"
    job.started_at = datetime.now(timezone.utc)
    job.error_message = None

    image_ids = list(
        db.scalars(
            select(Image.id)
            .where(
                Image.processing_status == "pending"
            )
            .order_by(Image.id)
        )
    )

    job.total_items = len(image_ids)
    job.processed_items = 0
    job.failed_items = 0

    db.commit()

    for image_id in image_ids:
        success = False
        final_error = None

        for retry_number in range(
            1,
            MAX_RETRIES + 1,
        ):
            image = db.get(
                Image,
                image_id,
            )

            if image is None:
                final_error = "Image record not found."
                break

            print(
                f"[Job {job_id}] "
                f"Processing {image.filename} "
                f"({retry_number}/{MAX_RETRIES})"
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
                final_error = str(error)

                print(
                    f"[Job {job_id}] "
                    f"Failed {image.filename}: "
                    f"{error}"
                )

                if retry_number < MAX_RETRIES:
                    retry_image = db.get(
                        Image,
                        image_id,
                    )

                    if retry_image is not None:
                        retry_image.processing_status = (
                            "pending"
                        )
                        db.commit()

                    wait_seconds = (
                        2 ** retry_number
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
                "Processing job no longer exists."
            )

        if success:
            job.processed_items += 1

        else:
            job.failed_items += 1

            failed_image = db.get(
                Image,
                image_id,
            )

            if failed_image is not None:
                failed_image.processing_status = (
                    "failed"
                )

                failed_image.last_error = (
                    final_error
                )

        db.commit()

        finished_items = (
            job.processed_items
            + job.failed_items
        )

        print(
            f"Progress: "
            f"{finished_items}/{job.total_items}"
        )

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
            f"{job.failed_items} image(s) "
            f"failed after retries."
        )

    else:
        job.status = "completed"

    job.completed_at = datetime.now(
        timezone.utc
    )

    db.commit()

    print()
    print(
        f"Job {job_id} finished: "
        f"{job.status}"
    )


def main() -> None:
    print("Image processing worker started.")
    print("Waiting for jobs...")

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
            print("Worker stopped.")
            break

        except Exception as error:
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
