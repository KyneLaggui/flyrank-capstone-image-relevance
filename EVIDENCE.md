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
