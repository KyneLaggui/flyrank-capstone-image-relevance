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
