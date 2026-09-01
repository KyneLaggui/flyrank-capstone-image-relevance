from decimal import Decimal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    postgres_db: str
    postgres_user: str
    postgres_password: str
    database_url: str

    vision_provider: str = "ollama"

    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "gemma3:4b"

    embedding_model: str = "all-minilm"

    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.7-flash"

    vision_confidence_threshold: float = 0.70

    match_similarity_threshold: float = 0.55

    gemini_input_price_per_million: Decimal = Decimal("0.75")
    gemini_output_price_per_million: Decimal = Decimal("3.75")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()  # pyright: ignore[reportCallIssue]
