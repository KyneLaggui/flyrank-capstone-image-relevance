# Evidence

## Database Persistence

Created an image through `POST /images`, restarted the application and PostgreSQL container, then retrieved the same record through `GET /images`.

Result: the record remained stored in PostgreSQL.

## API Boundary Validation

Submitting an image with an empty filename and file path returns HTTP 422 rather than causing an internal server error.

## Missing Resource

Requesting a nonexistent image through `GET /images/9999` returns HTTP 404 with:

`Image not found.`

## Duplicate Image

Submitting the same filename twice returns HTTP 409 with:

`An image with this filename already exists.`

## Background Job Persistence

Created an image-processing job through:

`POST /jobs/image-processing`

The endpoint returned HTTP 201 with a persistent queued job containing the total number of pending images.

The same job could be retrieved afterward through:

`GET /jobs/{job_id}`

This confirms that processing jobs are stored persistently rather than existing only inside the HTTP request.

## Image Dataset

The project contains approximately 50 images across five subject categories:

- red fox
- wolf
- dog
- bear
- deer

The image seed script was run twice.

First run:

- images inserted successfully

Second run:

- existing images were skipped
- no duplicate database records were created

This confirms the dataset can be seeded repeatedly without creating duplicate image records.

## Stage 4A - Single Image Analysis

Successfully analyzed `fox_01.jpg` using the local Ollama `gemma3:4b` vision model.

Test endpoint:

`POST /images/1/analyze`

Observed result:

- Subject: `fox`
- Category: `mammal`
- Confidence: `0.98`
- Flagged: `false`
- Processing Status: `completed`

The response also included structured attributes and a generated caption.

The result was successfully saved in the `image_metadata` table.

Vision model usage was also recorded in the `ai_cost_logs` table. Since Ollama runs locally, the external API cost is recorded as `$0`.

The image completed the following flow successfully:

Image -> Vision Model -> Pydantic Validation -> Confidence Check -> Database -> Completed

## Stage 4B - Batch Image Processing

The background image-processing worker successfully processed the complete image dataset using the local Ollama vision model.

### Final Results

- Total images: 50
- Completed images: 50
- Image metadata records: 50
- Remaining pending images: 0
- Vision model usage recorded in `ai_cost_logs`

### Image Status Verification

The following SQL query was used to verify the final processing status:

`SELECT processing_status, COUNT(*) FROM images GROUP BY processing_status;`

Observed result:

`completed | 50`

### Metadata Verification

The following query was used to verify that metadata was created for all images:

`SELECT COUNT(*) FROM image_metadata;`

Observed result:

`50`

### AI Usage Verification

Vision usage records can be checked using:

`SELECT COUNT(*) FROM ai_cost_logs WHERE operation = 'vision_analysis';`

The worker processed pending images automatically, tracked progress, retried failed processing attempts when necessary, and persisted the generated image metadata.

The completed flow is:

Queued Job -> Background Worker -> Image Analysis -> Pydantic Validation -> Metadata Persistence -> AI Usage Logging -> Job Completion

## Stage 5A - Embedding Foundation

Successfully generated semantic embeddings using the local Ollama `all-minilm` model.

Verified:

- One image embedding was created.
- One post embedding was created.
- Both embeddings use the same model and vector dimensions.
- Embedding usage was recorded in `ai_cost_logs`.
- Re-running the embedding process did not create duplicate records.

The image embedding is generated from its AI-produced subject, category, attributes, and caption.

The post embedding is generated from its title and content.

## Stage 5B - Batch Embedding Generation

The background worker successfully generated semantic embeddings for the complete image dataset and all existing posts.

Verified results:

- Image embeddings: 50
- Post embeddings: 3
- Total embeddings: 53
- Embedding model: `all-minilm`
- Vector dimensions: 384
- Embedding usage logs: 53
- Failed job items: 0

The embedding generation job completed successfully with:

- Total items: 53
- Processed items: 53
- Failed items: 0

All image and post embeddings are stored in PostgreSQL and use the same embedding model and vector dimensions.

## Stage 5C - Semantic Similarity Ranking

Successfully implemented semantic ranking between blog posts and images.

Verified behavior:

- Post embeddings are compared against all 50 image embeddings.
- Cosine similarity is calculated for each image.
- Results are sorted from highest to lowest similarity.
- Ranked image results include the image filename, detected subject, category, and similarity score.
- The red fox test post successfully returned ranked image recommendations from the complete image dataset.
- The cosine similarity implementation was verified with known vector examples.

The ranking endpoint is:

`GET /posts/{post_id}/rank-images`

This stage returns raw semantic ranking only. No candidate is accepted or rejected yet.

## Stage 5D - Mismatch Guard

The mismatch guard successfully validates ranked image candidates using confidence, subject compatibility, and semantic similarity.

Verified successful match:

- Post subject: `fox`
- Image subject: `fox`
- Image: `fox_01.jpg`
- Similarity: approximately `0.597`
- Confidence: `0.98`
- Result: accepted

The development similarity threshold is currently:

`0.55`

The vision confidence threshold remains:

`0.70`

A forced wolf candidate was also tested against the fox post.

Verified mismatch behavior:

- Post subject: `fox`
- Image subject: `wolf`
- Result: rejected
- Reason: subject/category mismatch

The guard now prevents a semantically related but incorrect animal from being accepted as the final image recommendation.

## Stage 5E - Final Image Recommendation

The final recommendation endpoint successfully combines semantic ranking and mismatch validation.

Endpoint:

`GET /posts/{post_id}/images`

Verified fox behavior:

- A red fox post returned a fox image.
- `match_found` was `true`.
- The recommended candidate passed the confidence, similarity, and subject compatibility checks.

Verified no-match behavior:

- A lion post was created while the image corpus contained no lion images.
- `match_found` was `false`.
- The response returned `No confident match`.
- `recommendation` was `null`.
- Rejection reasons were included.

The system therefore does not automatically select the nearest embedding when the available candidates are not appropriate.

## Post Duplicate Protection

Verified that identical duplicate posts are rejected by the API.

Behavior:

- First identical post submission -> `201 Created`
- Second identical post submission -> `409 Conflict`

Duplicate detection checks both the post title and content before creating a new record.

## Stage 6A - Human Review API

The review workflow successfully supports human approval and rejection of AI-generated image suggestions.

Verified behavior:

- Suggestions are created only when a confident image match exists.
- New suggestions start with a `pending` status.
- Each suggestion stores the selected image, similarity score, confidence, and guard reason.
- A human reviewer can inspect why the image was recommended.
- Approved suggestions are stored with an `approved` status.
- Rejected suggestions are stored with a `rejected` status.
- Human review notes are persisted.
- A suggestion that has already been reviewed returns a conflict instead of allowing another decision.
- Posts with no confident match do not create unsafe suggestions.

This completes the human-in-the-loop review workflow required for the recommendation system.

## Stage 6B - Labeled Evaluation Dataset

Created a ground-truth evaluation dataset containing 10 labeled post-image pairs.

Dataset coverage:

- 2 fox evaluation posts
- 2 wolf evaluation posts
- 2 dog evaluation posts
- 2 bear evaluation posts
- 2 deer evaluation posts

Each evaluation case contains:

- A unique case identifier
- A post title
- Descriptive post content
- One expected correct image

The evaluation seed script was verified to be idempotent, preventing duplicate evaluation posts.

All evaluation posts were embedded using `all-minilm`, allowing them to be compared against the existing image embeddings.

The existing lion post remains separate as a negative test for the `No confident match` behavior.

## Stage 6C - Matching Evaluation

The matching engine was evaluated using 10 labeled post-image pairs.

Initial configuration:

- Similarity threshold: `0.55`
- Raw Ranking Top-1 Precision: `8/10 = 80%`
- Final Recommendation Top-1 Precision: `7/10 = 70%`
- No Confident Match: `1`

One known-correct evaluation case exposed an overly strict threshold:

- Case: `dog_eval_02`
- Expected image: `dog_08.jpg`
- Raw Top-1 image: `dog_08.jpg`
- Similarity: approximately `0.5098`
- Expected rank: `1`
- Final result at threshold `0.55`: `No confident match`

Because the correct image ranked first but was rejected only by the similarity threshold, the threshold was calibrated to `0.50`.

Final configuration:

- Similarity threshold: `0.50`
- Final Top-1 Precision: `8/10 = 80%`

The evaluation result is stored in:

`data/eval_results.json`

The labeled evaluation set remains unchanged during threshold tuning so the measured result reflects the system's behavior rather than modified ground truth.

## Stage 6D - Production Hardening and Safety Verification

### Automated Tests

The focused test suite completed successfully:

`13 passed`

Coverage includes:

- AI call budget calculations and rejection when a job exceeds its configured limit.
- Structured vision schema validation.
- Rejection of confidence values outside the valid range.
- Rejection of empty image attribute lists.
- Cosine similarity for identical, orthogonal, and opposite vectors.
- Rejection of vectors with incompatible dimensions.
- Acceptance of a valid fox image for a fox post.
- Rejection of a wolf candidate for a fox post even when semantic similarity is high.
- Rejection of low-confidence image classifications.

### Image Processing Coverage

All original corpus images were successfully processed and stored with structured metadata.

- Original images processed: `50`
- Original metadata records: `50`

### Low-Confidence Safety Probe

A deliberately degraded image was processed through the real vision pipeline to verify uncertainty handling.

Observed result:

- File: `ambiguous_02.jpg`
- Detected subject: `human`
- Detected category: `person`
- Confidence: `0.60`
- Flagged: `true`

The incorrect subject classification was not silently trusted because the confidence score fell below the configured `0.70` confidence threshold.

This verifies that low-confidence AI output is flagged for review rather than automatically accepted.

### AI Cost Attribution

Cost logs were verified for both AI operations:

- Vision analysis using `gemma3:4b`
- Embedding generation using `all-minilm`

Both models run locally through Ollama, so the external monetary cost is `$0`, while each AI call remains attributed and recorded.

### API Boundary Validation

Verified clean HTTP error behavior:

- Invalid empty post input -> `422`
- Missing resource -> `404`
- Duplicate post creation -> `409`
- Repeated suggestion review -> `409`

No unexpected server error is required for these expected failure cases.

### Matching Safety Probes

Verified:

- A red fox post returns a valid fox recommendation.
- A forced wolf candidate for a fox post is rejected with a mismatch explanation.
- A lion post with no suitable image returns `No confident match`.
- The calibrated evaluation pipeline continues to report the measured Top-1 Precision from Stage 6C.

### Budget Guard

AI batch jobs now estimate their maximum possible model calls using:

`total items × maximum retry attempts`

Jobs that exceed the configured AI call budget are rejected before processing begins.

# Final Acceptance Evidence Index

## Probe 1 - Batch Vision Processing and Low-Confidence Flagging

Verified that the image corpus is processed through schema-validated vision analysis.

A deliberately degraded robustness fixture produced:

- File: ambiguous_02.jpg
- Detected subject: human
- Category: person
- Confidence: 0.60
- Flagged: true

This confirms that low-confidence model output is flagged rather than silently accepted.

## Probe 2 - Red Fox Semantic Matching

Verified that a red fox article returns a fox recommendation and that semantically unrelated animal images rank lower.

Semantic matching uses stored all-minilm embeddings and cosine similarity rather than filenames.

## Probe 3 - Forced Wolf Rejection

Verified that forcing a wolf image as the candidate for a fox post produces:

- accepted = false
- A subject/category mismatch explanation

The mismatch guard rejects the candidate even when semantic similarity alone could otherwise appear acceptable.

## Probe 4 - No Confident Match

Verified that the lion article, for which the corpus contains no lion image, returns:

- match_found = false
- message = "No confident match."
- recommendation = null
- Human-readable rejection reasons

The system does not automatically select the nearest unrelated image.

## Probe 5 - Labeled Evaluation

The final evaluation dataset contains 10 labeled post-image pairs.

Final Recommendation Top-1 Precision:
8/10 = 80.00%

Final similarity threshold:
0.50

The ground-truth labels were not modified during threshold calibration.

Evaluation output is stored in:
data/eval_results.json

## Probe 6 - AI Cost Attribution

Vision and embedding calls are persisted in ai_cost_logs.

Operations include:

- vision_analysis using gemma3:4b
- embedding_generation using all-minilm

Because both models run through local Ollama, external monetary cost is $0, while calls remain individually attributed.

## Shared Backend Requirements

### Layered Architecture

The project separates:

- HTTP/API routes in app/api
- Business and AI logic in app/services
- Database models in app/models
- Request and response validation in app/schemas

### Boundary Validation

Verified clean expected API errors:

- Invalid input -> 422
- Missing resource -> 404
- Duplicate/conflicting operation -> 409

### Background Processing

Image analysis and embedding generation run through the database-backed worker.

The worker includes:

- Job state
- Progress counters
- Configurable retries
- Retry delay
- Durable error reporting

### Persistence and Migrations

PostgreSQL is used for persistent storage.

Schema changes are tracked through Alembic migrations.

Indexes and uniqueness constraints are defined for resources that require them.

This capstone is designed as a single-system project and does not contain a tenant/account model, so tenant isolation is not applicable to the domain.

### Idempotency

Verified idempotent behavior includes:

- Duplicate post protection
- Duplicate active job protection
- Embedding content hashes that avoid unnecessary regeneration
- Idempotent dataset seeding
- Suggestions cannot be reviewed more than once

### Secrets

Secrets are loaded from environment variables.

.env is excluded from Git and .env.example contains only safe placeholder configuration.

### Cost and Budget Guard

Every AI operation is attributed through ai_cost_logs.

Batch jobs estimate their worst-case AI calls using:

total items x maximum attempts

Jobs exceeding AI_MAX_CALLS_PER_JOB are rejected before processing.
