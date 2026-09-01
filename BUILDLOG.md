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
