from pathlib import Path

from PIL import Image


SOURCE_DIR = Path("data/images")
OUTPUT_DIR = Path("data/prepared_images")

MAX_SIZE = (1024, 1024)
JPEG_QUALITY = 80


def prepare_image(source_path: Path, output_path: Path) -> None:
    with Image.open(source_path) as source_image:
        image = source_image.convert("RGB")
        image.thumbnail(MAX_SIZE)

        image.save(
            output_path,
            format="JPEG",
            quality=JPEG_QUALITY,
            optimize=True,
        )


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    image_files = sorted(SOURCE_DIR.glob("*.jpg"))

    if not image_files:
        print("No JPG images found.")
        return

    successful = 0
    failed = 0

    for source_path in image_files:
        output_path = OUTPUT_DIR / source_path.name

        try:
            prepare_image(source_path, output_path)
            print(f"Prepared: {source_path.name}")
            successful += 1

        except Exception as error:
            print(f"Failed: {source_path.name}")
            print(f"Reason: {error}")
            failed += 1

    print()
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Total: {len(image_files)}")


if __name__ == "__main__":
    main()
