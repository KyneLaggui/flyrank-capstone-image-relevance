# AI Image Understanding & Content Matching Engine

## Problem

Content systems may contain many images, making it difficult to manually select a relevant image for every article. Simple filename or keyword matching can also produce incorrect recommendations.

This project builds a backend system that understands images using a vision model, generates semantic embeddings, and matches images to blog posts based on meaning. A mismatch guard rejects low-confidence or incorrect matches instead of blindly returning the closest candidate.

## Core Dataset

Approximately 50 images across five categories:

- Red fox
- Wolf
- Dog
- Bear
- Deer

Approximately 10 images will be collected for each category.

## Image Metadata Schema

Each processed image will contain:

- subject
- category
- attributes
- caption
- confidence

Low-confidence or invalid AI results will be flagged rather than silently accepted.

## Core Data Model

The system will initially use the following entities:

- Image
- ImageMetadata
- Post
- Embedding
- ProcessingJob
- Suggestion
- Review
- AICostLog

## Matching Strategy

1. Analyze images using a vision model.
2. Validate the structured response.
3. Generate embeddings from image captions.
4. Generate an embedding for each blog post.
5. Compare post and image embeddings using cosine similarity.
6. Rank candidate images.
7. Run candidates through the mismatch guard.
8. Return a ranked recommendation or `no confident match`.

## Mismatch Guard

The guard initially evaluates:

- vision confidence
- semantic similarity
- subject/category compatibility

Candidates that fail the guard are rejected with a human-readable reason.

Threshold values will be tuned later using the labeled evaluation dataset.

## API Surface

Initial endpoints:

- `GET /health`
- `POST /images`
- `GET /images`
- `GET /images/{image_id}`
- `POST /posts`
- `GET /posts`
- `GET /posts/{post_id}`

Later phases will add:

- image-processing jobs
- semantic matching
- suggestions
- approve/reject review endpoints

## Architecture

HTTP/API Layer
↓
Service/Business Logic Layer
↓
Database Layer
↓
PostgreSQL

Slow AI processing will run through background jobs rather than blocking API requests.

## Non-Goals

The core project will not include:

- a production-quality frontend
- very large-scale image storage or retrieval
- multiple model comparison
- automatic image generation

The focus is reliable image understanding, semantic matching, and safe rejection.
