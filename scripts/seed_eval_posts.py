import json
from pathlib import Path

from sqlalchemy import select

from app.db import SessionLocal
from app.models.image import Image
from app.models.post import Post


EVAL_PATH = Path("data/eval_posts.json")


def main() -> None:
    with EVAL_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        cases = json.load(file)

    if len(cases) < 10:
        raise ValueError(
            "Evaluation dataset must contain "
            "at least 10 cases."
        )

    db = SessionLocal()

    inserted = 0
    skipped = 0

    try:
        for case in cases:
            expected_image = db.scalar(
                select(Image).where(
                    Image.filename
                    == case["expected_image"]
                )
            )

            if expected_image is None:
                raise ValueError(
                    "Expected image does not exist: "
                    f"{case['expected_image']}"
                )

            existing_post = db.scalar(
                select(Post).where(
                    Post.title == case["title"],
                    Post.content == case["content"],
                )
            )

            if existing_post is not None:
                print(
                    f"Skipped: {case['case_id']}"
                )
                skipped += 1
                continue

            post = Post(
                title=case["title"],
                content=case["content"],
            )

            db.add(post)

            print(
                f"Inserted: {case['case_id']}"
            )

            inserted += 1

        db.commit()

    finally:
        db.close()

    print()
    print(f"Inserted: {inserted}")
    print(f"Skipped: {skipped}")


if __name__ == "__main__":
    main()
