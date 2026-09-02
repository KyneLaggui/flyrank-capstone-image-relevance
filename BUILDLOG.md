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

## Stage 5A - Embedding Foundation

Implemented the initial semantic embedding pipeline using the local Ollama `all-minilm` model.

- Added an `embeddings` database table for image and post vectors.
- Added local text embedding generation through Ollama.
- Added semantic text construction from image metadata and post content.
- Added content hashing to avoid regenerating unchanged embeddings.
- Added AI usage logging for embedding generation.
- Successfully generated and stored an embedding for `fox_01.jpg`.
- Successfully generated and stored an embedding for the red fox test post.
- Verified that repeated processing does not create duplicate embeddings or usage logs.

## Stage 5B - Batch Embedding Generation

Implemented background batch generation for semantic embeddings.

- Extended the background worker to support embedding-generation jobs.
- Generated embeddings for all completed images and existing posts.
- Reused existing embeddings when the source content had not changed.
- Added retry handling and progress tracking for embedding generation.
- Continued recording model usage and local inference cost information in `ai_cost_logs`.

Final result:

- 50 image embeddings
- 3 post embeddings
- 53 total embeddings
- All embeddings use `all-minilm`
- All embeddings have 384 dimensions
- 53 embedding usage logs recorded
- 0 failed items

## Stage 5C - Semantic Similarity Ranking

Implemented semantic image ranking using cosine similarity.

- Added cosine similarity calculation for stored embedding vectors.
- Added ranking logic that compares a post embedding against all image embeddings.
- Added sorting from highest to lowest semantic similarity.
- Added an API endpoint for retrieving ranked image suggestions for a post.
- Added validation for missing embeddings and incompatible vector dimensions.
- Verified the cosine similarity implementation using identical, unrelated, and opposite vectors.
- Successfully tested ranking using the red fox post against the complete image dataset.

This stage provides raw semantic ranking only. Acceptance and rejection rules will be added separately in the mismatch guard.

## Stage 5D - Mismatch Guard

Implemented the mismatch guard for validating ranked image candidates.

- Added image confidence validation.
- Added subject normalization for fox, wolf, dog, bear, and deer.
- Added semantic similarity threshold checking.
- Added subject compatibility checking between posts and images.
- Added human-readable rejection reasons.
- Added an endpoint for testing a specific image against a post.
- Set the temporary development similarity threshold to `0.55` after testing a valid fox-to-fox match.
- Kept the vision confidence threshold separate at `0.70`.

Verified behavior:

- Fox post + fox image -> accepted
- Fox post + wolf image -> rejected because of subject mismatch

The similarity threshold is temporary and will be tuned later using the labeled evaluation dataset.

## Stage 5E - Final Image Recommendation

Implemented the final image recommendation flow by combining semantic ranking with the mismatch guard.

- Added a recommendation service that evaluates ranked image candidates.
- Added a final endpoint for retrieving safe image recommendations for a post.
- Candidates are checked using image confidence, subject compatibility, and semantic similarity.
- The system skips rejected candidates instead of automatically trusting the highest similarity score.
- Added support for returning `No confident match` when no image passes the guard.
- Added human-readable rejection reasons for unsuccessful candidates.

Verified behavior:

- Red fox post -> returns an accepted fox image.
- Lion post with no lion images -> returns `No confident match`.
- Incorrect candidates are rejected instead of being returned as recommendations.

This completed the core matching engine.

## Post Duplicate Protection

Added duplicate protection to the post creation endpoint.

- The API now checks for an existing post with the same title and content.
- Identical duplicate posts return `409 Conflict` instead of creating another record.
- Existing duplicate test data was cleaned up manually from PostgreSQL.

## Stage 6A - Human Review API

Implemented the human review workflow for image suggestions.

- Added persistent suggestion records for recommended post-image pairs.
- Added review records for approved and rejected suggestions.
- Added endpoints to create, inspect, approve, and reject suggestions.
- Added protection against reviewing the same suggestion more than once.
- Added validation so suggestions rejected by the mismatch guard cannot be approved.
- Added human review notes for approval and rejection decisions.
- Verified that safe AI-generated suggestions can be reviewed independently by a human.

Verified behavior:

- A recommended image can be saved as a pending suggestion.
- A human can inspect why the image was selected.
- A pending suggestion can be approved.
- A pending suggestion can be rejected.
- Reviewed suggestions cannot be reviewed again.
- Posts with no confident match do not create a suggestion.
