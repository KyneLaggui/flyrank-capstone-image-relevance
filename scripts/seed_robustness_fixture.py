from pathlib import Path

from sqlalchemy import select

from app.db import SessionLocal
from app.models.image import Image


FILENAME = "ambiguous_02.jpg"

FILE_PATH = Path(
    "data/prepared_images/ambiguous_02.jpg"
)


def main() -> None:
    if not FILE_PATH.exists():
        raise FileNotFoundError(
            f"Robustness fixture not found: "
            f"{FILE_PATH}"
        )

    db = SessionLocal()

    try:
        existing = db.scalar(
            select(Image).where(
                Image.filename == FILENAME
            )
        )

        if existing is not None:
            print(
                "Skipped robustness fixture: "
                "already exists."
            )
            return

        image = Image(
            filename=FILENAME,
            file_path=FILE_PATH.as_posix(),
            processing_status="pending",
        )

        db.add(image)
        db.commit()

        print("Inserted robustness fixture:")
        print(FILENAME)

    finally:
        db.close()


if __name__ == "__main__":
    main()
