from dataclasses import dataclass

from ollama import Client

from app.config import settings


@dataclass
class EmbeddingResult:
    vector: list[float]
    input_tokens: int


class EmbeddingService:
    def __init__(self) -> None:
        self.client = Client(
            host=settings.ollama_host
        )

    def embed_text(
        self,
        text: str,
    ) -> EmbeddingResult:
        cleaned_text = " ".join(
            text.split()
        )

        if not cleaned_text:
            raise ValueError(
                "Cannot generate an embedding from empty text."
            )

        response = self.client.embed(
            model=settings.embedding_model,
            input=cleaned_text,
        )

        if not response.embeddings:
            raise ValueError(
                "Ollama returned no embedding."
            )

        vector = list(
            response.embeddings[0]
        )

        return EmbeddingResult(
            vector=vector,
            input_tokens=(
                response.prompt_eval_count or 0
            ),
        )
