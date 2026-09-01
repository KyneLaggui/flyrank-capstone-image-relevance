from sqlalchemy import select

from app.db import SessionLocal
from app.models.image import Image
from app.models.post import Post
from app.services.embedding_processing import (
    embed_image,
    embed_post,
)


def main() -> None:
    db = SessionLocal()

    try:
        image = db.scalar(
            select(Image).where(
                Image.filename == "fox_01.jpg"
            )
        )

        if image is None:
            raise RuntimeError(
                "fox_01.jpg was not found."
            )

        post = db.scalar(
            select(Post)
            .where(
                Post.title
                == "Red Fox Behavior and Habitat"
            )
            .order_by(Post.id.desc())
        )

        if post is None:
            raise RuntimeError(
                "Red fox test post was not found."
            )

        image_embedding = embed_image(
            db=db,
            image=image,
        )

        post_embedding = embed_post(
            db=db,
            post=post,
        )

        print(
            "Image embedding:"
        )
        print(
            f"ID: {image_embedding.id}"
        )
        print(
            f"Dimensions: "
            f"{image_embedding.dimensions}"
        )

        print()

        print(
            "Post embedding:"
        )
        print(
            f"ID: {post_embedding.id}"
        )
        print(
            f"Dimensions: "
            f"{post_embedding.dimensions}"
        )

    finally:
        db.close()


if __name__ == "__main__":
    main()
