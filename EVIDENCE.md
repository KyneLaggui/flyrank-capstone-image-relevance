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
