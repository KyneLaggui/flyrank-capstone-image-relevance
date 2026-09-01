# Build Log

## Stage 1 — Project Setup

- Created the FastAPI project and health endpoint.
- Added PostgreSQL using Docker Compose.
- Connected FastAPI to PostgreSQL using SQLAlchemy.
- Used AI assistance to understand the capstone requirements, structure the project, and draft the initial architecture.
- Reviewed and implemented each setup step manually.

## Stage 1C — System Design

- Defined the initial dataset and project scope.
- Designed the major database entities.
- Defined the first version of the semantic matching pipeline.
- Defined the mismatch guard concept before implementation.
- Kept threshold values undecided until an evaluation dataset exists.

## Stage 2A — Database Foundation

- Added SQLAlchemy models for images, image metadata, and posts.
- Separated original image records from AI-generated metadata.
- Used PostgreSQL JSONB for image attributes.
- Configured Alembic to use the application's environment-based database configuration.
- Generated and applied the first database migration.
- Verified both migration upgrade and downgrade behavior.

## Stage 2B — Image and Post APIs

- Added Pydantic request and response schemas for images and posts.
- Added database-backed endpoints for creating and retrieving images.
- Added database-backed endpoints for creating and retrieving posts.
- Added duplicate filename handling using HTTP 409.
- Added clean HTTP 404 responses for missing resources.
- Verified Pydantic validation returns HTTP 422 for invalid input.
- Verified records survive FastAPI and PostgreSQL container restarts.

## Stage 2C — Background Job and AI Cost Foundation

- Added persistent processing job records for asynchronous image processing.
- Added progress fields for total, processed, and failed items.
- Added retry-related fields to image records.
- Added an AI cost log model for per-call usage and cost attribution.
- Added endpoints for creating and inspecting image-processing jobs.
- Kept job execution separate from job creation so the future worker can support retries, progress, and failures.

## Stage 3 — Image Dataset

- Collected approximately 50 images across red fox, wolf, dog, bear, and deer categories.
- Recorded image provenance and human ground-truth labels in `images_manifest.json`.
- Kept human labels separate from the AI runtime pipeline to avoid leaking answers into image classification.
- Normalized image dimensions and JPEG size to keep the corpus inexpensive and reproducible.
- Added an idempotent seed script for registering image records in PostgreSQL.
- Verified that all seeded images begin with `pending` processing status.

## Stage 4A - Single Image Analysis

Implemented the first working image analysis flow using a local Ollama vision model.

- Added structured image analysis with subject, category, attributes, caption, and confidence.
- Added Pydantic validation for the model output.
- Added confidence-based flagging for low-confidence results.
- Added database persistence for generated image metadata.
- Added AI usage logging in `ai_cost_logs`.
- Added `POST /images/{image_id}/analyze` for testing individual images.
- Added protection against reprocessing already completed images.
- Added error handling using processing status, attempt count, and `last_error`.

Initially tested Gemini for image analysis, but the free-tier request quota was reached. Switched the vision provider to local Ollama using `gemma3:4b` so the dataset can be processed without depending on an external API quota.

Successfully tested the pipeline using `fox_01.jpg`. The model identified the subject as `fox` with a confidence score of `0.98`, and the result was successfully saved to PostgreSQL.

## Stage 4B - Batch Image Processing

Implemented background batch processing for the image understanding pipeline.

- Added a database-backed worker that processes queued image-processing jobs.
- Added automatic processing of all pending images.
- Added retry handling for failed image-analysis attempts.
- Added job progress tracking using total, processed, and failed item counts.
- Added protection against creating multiple active image-processing jobs.
- Reused the existing Ollama image-analysis service for batch processing.
- Continued recording AI model usage for each successfully processed image.

The batch successfully processed the remaining image dataset.

Final result:

- 50 images completed
- 50 image metadata records created
- Vision usage logs recorded
- No remaining pending images
