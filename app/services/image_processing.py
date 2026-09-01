import logging
from decimal import Decimal
from pathlib import Path

from sqlalchemy.orm import Session

from app.config import settings
from app.models.ai_cost_log import AICostLog
from app.models.image import Image, ImageMetadata
from app.services.vision import VisionService
from google.genai.errors import ClientError


logger = logging.getLogger(__name__)

vision_service = VisionService()


def calculate_estimated_cost(
    input_tokens: int,
    output_tokens: int,
) -> Decimal:
    input_cost = (
        Decimal(input_tokens)
        / Decimal("1000000")
        * settings.gemini_input_price_per_million
    )

    output_cost = (
        Decimal(output_tokens)
        / Decimal("1000000")
        * settings.gemini_output_price_per_million
    )

    return input_cost + output_cost


def process_image(
    db: Session,
    image: Image,
) -> ImageMetadata:
    image_id = image.id

    if (
        image.processing_status == "completed"
        and image.metadata_record is not None
    ):
        return image.metadata_record

    image.processing_status = "processing"
    image.processing_attempts += 1
    image.last_error = None

    db.commit()

    try:
        result = vision_service.analyze_image(
            Path(image.file_path)
        )

        analysis = result.analysis

        flagged = (
            analysis.confidence
            < settings.vision_confidence_threshold
        )

        metadata = image.metadata_record

        if metadata is None:
            metadata = ImageMetadata(
                image_id=image_id,
                subject=analysis.subject,
                category=analysis.category,
                attributes=analysis.attributes,
                caption=analysis.caption,
                confidence=analysis.confidence,
                flagged=flagged,
            )

            db.add(metadata)

        else:
            metadata.subject = analysis.subject
            metadata.category = analysis.category
            metadata.attributes = analysis.attributes
            metadata.caption = analysis.caption
            metadata.confidence = analysis.confidence
            metadata.flagged = flagged

        billable_output_tokens = (
            result.usage.output_tokens
            + result.usage.thinking_tokens
        )

        if settings.vision_provider == "ollama":
            estimated_cost = Decimal("0")
        else:
            estimated_cost = calculate_estimated_cost(
                input_tokens=result.usage.input_tokens,
                output_tokens=billable_output_tokens,
            )

        cost_log = AICostLog(
            operation="vision_analysis",
            model_name=(
                settings.ollama_model
                if settings.vision_provider == "ollama"
                else settings.gemini_model
            ),
            resource_type="image",
            resource_id=image_id,
            input_tokens=result.usage.input_tokens,
            output_tokens=billable_output_tokens,
            estimated_cost_usd=estimated_cost,
        )

        db.add(cost_log)

        image.processing_status = "completed"
        image.last_error = None

        db.commit()
        db.refresh(metadata)

        return metadata

    except ClientError as error:
        db.rollback()

        failed_image = db.get(Image, image_id)

        if failed_image is not None:
            if error.code == 429:
                failed_image.processing_status = "pending"
            else:
                failed_image.processing_status = "failed"

            failed_image.last_error = str(error)

            db.commit()

        raise

    except Exception as error:
        logger.exception(
            "Image processing failed for image_id=%s",
            image_id,
        )

        db.rollback()

        failed_image = db.get(Image, image_id)

        if failed_image is not None:
            failed_image.processing_status = "failed"
            failed_image.last_error = str(error)

            db.commit()

        raise
