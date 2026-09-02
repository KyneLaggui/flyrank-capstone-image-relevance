from pathlib import Path

from PIL import (
    Image,
    ImageEnhance,
    ImageFilter,
)


SOURCE_PATH = Path(
    "data/images/fox_06.jpg"
)

OUTPUT_PATH = Path(
    "data/prepared_images/ambiguous_02.jpg"
)


def main() -> None:
    if not SOURCE_PATH.exists():
        raise FileNotFoundError(
            f"Source image not found: {SOURCE_PATH}"
        )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with Image.open(SOURCE_PATH) as image:
        image = image.convert("RGB")

        width, height = image.size

        image = image.crop(
            (
                width // 3,
                height // 3,
                (width * 2) // 3,
                (height * 2) // 3,
            )
        )

        image = image.resize(
            (20, 20)
        )

        image = image.resize(
            (512, 512)
        )

        image = image.filter(
            ImageFilter.GaussianBlur(
                radius=20
            )
        )

        image = ImageEnhance.Contrast(
            image
        ).enhance(0.25)

        image = ImageEnhance.Brightness(
            image
        ).enhance(0.30)

        image.save(
            OUTPUT_PATH,
            format="JPEG",
            quality=80,
        )

    print(
        "Created ambiguous fixture:",
        OUTPUT_PATH,
    )


if __name__ == "__main__":
    main()
