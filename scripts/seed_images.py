import json
from pathlib import Path

from sqlalchemy import select

from app.db import SessionLocal
from app.models.image import Image


MANIFEST_PATH = Path("data/images_manifest.json")
IMAGE_DIR = Path("data/images")


def main() -> None:
    with MANIFEST_PATH.open("r", encoding="utf-8") as file:
        manifest = json.load(file)

    db = SessionLocal()

    inserted = 0
    skipped = 0

    try:
        for item in manifest:
            filename = item["filename"]
            image_path = IMAGE_DIR / filename

            if not image_path.exists():
                print(f"Missing file: {filename}")
                continue

            existing_image = db.scalar(
                select(Image).where(
                    Image.filename == filename
                )
            )

            if existing_image:
                print(f"Skipped: {filename}")
                skipped += 1
                continue

            image = Image(
                filename=filename,
                file_path=str(image_path).replace("\\", "/"),
            )

            db.add(image)
            inserted += 1

        db.commit()

    finally:
        db.close()

    print()
    print(f"Inserted: {inserted}")
    print(f"Skipped: {skipped}")


if __name__ == "__main__":
    main()
