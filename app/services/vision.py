from dataclasses import dataclass
from pathlib import Path

from ollama import Client

from app.config import settings
from app.schemas.image_analysis import ImageAnalysisResult


@dataclass
class VisionUsage:
    input_tokens: int
    output_tokens: int
    thinking_tokens: int


@dataclass
class VisionResult:
    analysis: ImageAnalysisResult
    usage: VisionUsage


class VisionService:
    def __init__(self) -> None:
        self.client = Client(
            host=settings.ollama_host
        )

    def analyze_image(
        self,
        image_path: Path,
    ) -> VisionResult:
        if not image_path.exists():
            raise FileNotFoundError(
                f"Image does not exist: {image_path}"
            )

        prompt = """
Analyze the primary subject visible in this image.

Return:
- subject: the most specific common name you can confidently identify
- category: the broad category of the subject
- attributes: 3 to 8 visible characteristics
- caption: one factual sentence describing the image
- confidence: a number from 0 to 1 representing how certain you are
  about the subject identification

Only use visual evidence from the image.
Do not guess when the image is ambiguous.
Lower the confidence score when identification is uncertain.

Return the result as JSON matching the required schema.
"""

        response = self.client.chat(
            model=settings.ollama_model,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                    "images": [
                        str(image_path.resolve())
                    ],
                }
            ],
            format=ImageAnalysisResult.model_json_schema(),
            options={
                "temperature": 0,
            },
        )

        if not response.message.content:
            raise ValueError(
                "Ollama returned an empty response."
            )

        analysis = ImageAnalysisResult.model_validate_json(
            response.message.content
        )

        return VisionResult(
            analysis=analysis,
            usage=VisionUsage(
                input_tokens=(
                    response.prompt_eval_count or 0
                ),
                output_tokens=(
                    response.eval_count or 0
                ),
                thinking_tokens=0,
            ),
        )
