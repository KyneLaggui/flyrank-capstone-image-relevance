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
