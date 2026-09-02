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

## Stage 6B - Labeled Evaluation Dataset

Created a labeled evaluation dataset for measuring image matching quality.

- Added 10 evaluation posts across five animal categories: fox, wolf, dog, bear, and deer.
- Added two evaluation cases per category.
- Assigned one known correct image to each evaluation post.
- Used visually descriptive post content so exact-image matching can be evaluated meaningfully.
- Added an idempotent evaluation post seeding script.
- Verified that all expected images exist in the image corpus.
- Generated and stored embeddings for the evaluation posts using `all-minilm`.
- Kept the lion post separate as a negative no-match test case.

The evaluation dataset is now ready for automated Top-1 Precision measurement.

## Stage 6C - Evaluation and Threshold Calibration

Implemented an automated evaluation script for measuring image matching accuracy against the labeled evaluation dataset.

- Evaluated 10 labeled post-image pairs.
- Measured both raw semantic ranking and the final recommendation after the mismatch guard.
- Initial evaluation at a `0.55` similarity threshold produced:
  - Raw Top-1 Precision: 80%
  - Final Recommendation Top-1 Precision: 70%
  - 1 correct match was rejected as "No confident match."
- Investigated the rejected case and found that the correct `dog_08.jpg` image ranked first with a similarity score of approximately `0.5098`.
- Adjusted the similarity threshold from `0.55` to `0.50` based on the labeled evaluation data.
- Re-ran the evaluation after calibration.
- Final Top-1 Precision: 80% (8/10).
- Kept subject/category mismatch validation separate from the semantic similarity threshold to preserve protection against incorrect cross-category matches.

The final threshold was selected from measured evaluation behavior rather than manually choosing a value without evidence.

## Stage 6D - Production Hardening and Tests

Hardened the image matching backend and added focused automated tests for the system's critical behavior.

- Added an AI call budget guard for image-processing and embedding-generation jobs.
- Centralized the maximum retry count in application configuration so the worker and budget calculation use the same limit.
- Preserved background-job retries, progress tracking, and durable failure reporting.
- Added stronger post input validation for empty and oversized content.
- Added Pytest configuration so automated tests are isolated from manual scripts.
- Added tests for:
  - AI call budget enforcement
  - Structured vision output validation
  - Confidence bounds and required attributes
  - Cosine similarity behavior
  - Vector dimension mismatch handling
  - Correct fox acceptance
  - Forced wolf rejection
  - Low-confidence image rejection
- Automated test suite completed successfully with 13 passing tests.
- Added degraded-image robustness fixtures to verify low-confidence handling.
- The first ambiguous fixture exposed model overconfidence, which led to clearer confidence-calibration instructions in the vision prompt.
- A second degraded image produced a confidence score of `0.60` and was correctly flagged because it fell below the `0.70` vision confidence threshold.
- Verified all image records have corresponding processed metadata.
- Verified AI calls are attributed in the cost log for both vision analysis and embedding generation.
- Verified clean API errors for invalid input, missing resources, duplicate operations, and repeated review decisions.
- Re-ran the required matching safety scenarios successfully.

Stage 6D confirms that unsafe or uncertain AI output is rejected or flagged rather than silently trusted.

## Stage 6E - Final Packaging and Submission Preparation

Completed the final capstone packaging and reproducibility review.

- Finalized the README with architecture, setup, run, seed, evaluation, test, API, and limitations documentation.
- Added capstone.yaml with the run command, seed command, test command, base URL, and evaluator-facing endpoints.
- Finalized .env.example with safe local configuration values and no secrets.
- Made the degraded low-confidence robustness fixture reproducible from the seeded image corpus.
- Documented the calibrated semantic similarity threshold of 0.50.
- Documented the measured Top-1 Precision from the labeled evaluation set.
- Confirmed the automated test suite passes with 13 tests.
- Confirmed low-confidence AI output is flagged rather than silently trusted.
- Confirmed the human review workflow supports suggestion inspection, approval, and rejection.
- Reviewed repository structure, secrets handling, dataset reproducibility, and submission requirements.

### AI-Assisted Development Notes

AI tools were used during development to help break the capstone into incremental stages, review implementation ideas, explain backend concepts, draft tests, and improve documentation.

AI-generated suggestions were not accepted without testing.

Notable corrections during development included:

- The initial Gemini implementation reached free-tier rate limits, so the vision pipeline was changed to local Ollama with gemma3:4b.
- The first semantic similarity threshold of 0.55 rejected a known-correct evaluation match, so the threshold was recalibrated to 0.50 using labeled evaluation results.
- A degraded image exposed vision-model overconfidence by being incorrectly classified with high confidence. The vision prompt was improved with explicit confidence-calibration rules and a second degraded fixture successfully produced a low-confidence result that was flagged.
- Automated tests and acceptance probes were used to verify AI-assisted implementation decisions before finalizing them.

The final system behavior and documentation are based on observed tests and evaluation results rather than assumed AI correctness.
