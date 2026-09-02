# AI Image Understanding & Content Matching Engine

A FastAPI backend that uses vision AI and semantic embeddings to understand an image library and safely match images to blog posts.

The goal is not simply to return the closest image. The system must also know when **not** to recommend one. A mismatch guard combines semantic similarity, subject compatibility, and vision confidence so incorrect or uncertain matches can be rejected with a clear reason.

---

## Project Highlights

- Structured image understanding with `gemma3:4b`
- Semantic embeddings with `all-minilm`
- Pydantic validation for AI output
- Low-confidence image flagging
- Cosine-similarity image ranking
- Subject-aware mismatch protection
- Human approval/rejection workflow
- PostgreSQL persistence with Alembic migrations
- Database-backed background jobs with retries
- Per-call AI cost tracking
- AI-call budget guard
- Labeled evaluation set
- Focused automated tests

---

## Evaluation Result

<!-- Keep this number synchronized with: python -m scripts.evaluate_matching -->

| Metric                      |         Result |
| --------------------------- | -------------: |
| Labeled evaluation cases    |             10 |
| Final Top-1 Precision       | **80% (8/10)** |
| Similarity threshold        |         `0.50` |
| Vision confidence threshold |         `0.70` |
| Vision model                |    `gemma3:4b` |
| Embedding model             |   `all-minilm` |

The original similarity threshold was `0.55`.

During evaluation, a known-correct dog image ranked first with a similarity of about `0.5098`, but the guard rejected it because the threshold was too high. The threshold was therefore calibrated to `0.50` using the labeled evaluation set.

> Before submission, run `python -m scripts.evaluate_matching` and make sure the precision shown above exactly matches the script output.

---

## Architecture

```text
                          ┌──────────────────────┐
                          │      Image Files     │
                          └──────────┬───────────┘
                                     │
                                     v
                          ┌──────────────────────┐
                          │   Image Ingestion    │
                          └──────────┬───────────┘
                                     │
                                     v
                          ┌──────────────────────┐
                          │      PostgreSQL      │
                          └──────────┬───────────┘
                                     │
                                     v
                          ┌──────────────────────┐
                          │  Background Worker   │
                          └───────┬───────┬──────┘
                                  │       │
                    Vision        │       │ Embeddings
                                  v       v
                         ┌────────────┐  ┌────────────┐
                         │ gemma3:4b  │  │ all-minilm │
                         └─────┬──────┘  └─────┬──────┘
                               │               │
                               v               v
                    Structured Metadata   Image Embeddings
                               │               │
                               │               │
                               │         ┌─────┴────────────┐
                               │         │                  │
                               │         v                  v
                               │    Post Embeddings   Cosine Ranking
                               │                           │
                               └──────────────┬────────────┘
                                              v
                                   ┌──────────────────┐
                                   │  Mismatch Guard  │
                                   └────────┬─────────┘
                                            │
                           ┌────────────────┴────────────────┐
                           │                                 │
                           v                                 v
                 Safe recommendation                 Rejected candidate
                           │                                 │
                           v                                 v
                      Suggestion                    Human-readable reason
                           │
                           v
                    Human Review
                    /          \
                   v            v
               Approved      Rejected
```

### Layer Responsibilities

| Layer           | Responsibility                                                               |
| --------------- | ---------------------------------------------------------------------------- |
| `app/api/`      | HTTP routes and API responses                                                |
| `app/schemas/`  | Pydantic request/response and AI-output validation                           |
| `app/services/` | Vision, embeddings, matching, guard, review, and budget logic                |
| `app/models/`   | SQLAlchemy database models                                                   |
| `scripts/`      | Seeding, worker execution, evaluation, and data utilities                    |
| PostgreSQL      | Persistent application data, jobs, embeddings, suggestions, and AI cost logs |

Slow AI operations are handled by the background worker instead of blocking normal API requests.

---

# Getting Started

## 1. Prerequisites

Install:

- Python 3.12+
- Docker Desktop or Docker Engine with Docker Compose
- Ollama

Verify Ollama is running:

```bash
ollama --version
```

Pull the required local models:

```bash
ollama pull gemma3:4b
ollama pull all-minilm
```

Ollama normally runs at:

```text
http://localhost:11434
```

---

## 2. Clone and Create a Virtual Environment

```bash
git clone https://github.com/KyneLaggui/flyrank-capstone-image-relevance.git
python -m venv venv
```

### Windows PowerShell

```powershell
.\venv\Scripts\Activate.ps1
```

### Git Bash on Windows

```bash
source venv/Scripts/activate
```

### Linux / macOS

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## 3. Create the Environment File

### Git Bash / Linux / macOS

```bash
cp .env.example .env
```

### PowerShell

```powershell
Copy-Item .env.example .env
```

The default configuration uses PostgreSQL through Docker and local Ollama models.

---

## 4. Start PostgreSQL

```bash
docker compose up -d --wait
```

Apply database migrations:

```bash
alembic upgrade head
```

---

## 5. Seed Demo Data

Run the seed and fixture scripts in this order:

```bash
python -m scripts.seed_images
python -m scripts.create_ambiguous_fixture
python -m scripts.seed_robustness_fixture
python -m scripts.seed_eval_posts
```

What these commands do:

| Script                             | Purpose                                                    |
| ---------------------------------- | ---------------------------------------------------------- |
| `scripts.seed_images`              | Adds the main image corpus to the database                 |
| `scripts.create_ambiguous_fixture` | Creates the degraded image used for low-confidence testing |
| `scripts.seed_robustness_fixture`  | Adds that degraded fixture to the database                 |
| `scripts.seed_eval_posts`          | Adds the labeled evaluation posts                          |

These scripts are separate from the AI processing itself. Seeding creates database records; the background worker performs vision analysis and embedding generation.

---

## 6. Start the API

```bash
uvicorn app.main:app --reload
```

API base URL:

```text
http://127.0.0.1:8000
```

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

Health endpoint:

```text
GET /health
```

---

## 7. Start the Background Worker

Open a **second terminal**, activate the same virtual environment, then run:

```bash
python -m scripts.run_worker
```

Keep this terminal open while image-processing or embedding jobs are running.

The worker provides:

- Database-backed job processing
- Progress tracking
- Configurable retries
- Exponential retry delays
- Failure reporting
- AI-call logging

---

## 8. Process the Images

With the API and worker running, open Swagger:

```text
http://127.0.0.1:8000/docs
```

Run:

```text
POST /jobs/image-processing
```

This queues all pending images for vision analysis.

The worker will:

1. Load each pending image.
2. Send it to `gemma3:4b`.
3. Validate the structured AI response.
4. Store subject, category, attributes, caption, and confidence.
5. Flag results below the configured confidence threshold.
6. Record the AI call in the cost log.

Check job progress with:

```text
GET /jobs/{job_id}
```

---

## 9. Generate Embeddings

After image processing completes, queue the embedding job:

```text
POST /jobs/embedding-generation
```

The worker generates embeddings for:

- Completed image metadata
- Stored blog posts

The embedding model is:

```text
all-minilm
```

Content hashes are used to avoid unnecessary regeneration when the source content has not changed.

---

# Script Reference

The files below are executable Python modules. Run them from the project root with `python -m ...`.

| File                                  | Command                                      | When to use it                                                        |
| ------------------------------------- | -------------------------------------------- | --------------------------------------------------------------------- |
| `scripts/seed_images.py`              | `python -m scripts.seed_images`              | Seed the main image records                                           |
| `scripts/create_ambiguous_fixture.py` | `python -m scripts.create_ambiguous_fixture` | Create the degraded confidence-test fixture                           |
| `scripts/seed_robustness_fixture.py`  | `python -m scripts.seed_robustness_fixture`  | Register the degraded fixture in PostgreSQL                           |
| `scripts/seed_eval_posts.py`          | `python -m scripts.seed_eval_posts`          | Seed the labeled evaluation posts                                     |
| `scripts/run_worker.py`               | `python -m scripts.run_worker`               | Start the background worker                                           |
| `scripts/evaluate_matching.py`        | `python -m scripts.evaluate_matching`        | Run the labeled matching evaluation                                   |
| `scripts/prepare_images.py`           | `python -m scripts.prepare_images`           | Optional: prepare raw source images when the raw dataset is available |

> `POST /jobs/image-processing` and `POST /jobs/embedding-generation` are **API operations**, not Python scripts. Run them through Swagger or another HTTP client while `scripts.run_worker` is active.

---

# Matching API

## Raw Semantic Ranking

```text
GET /posts/{post_id}/rank-images
```

Returns images ordered by cosine similarity.

This is the raw semantic ranking before the safety guard makes the final decision.

---

## Inspect One Candidate

```text
GET /posts/{post_id}/check-image/{image_id}
```

Returns the mismatch-guard decision for a specific post/image pair.

The guard checks:

- Vision confidence
- Post subject
- Image subject
- Subject compatibility
- Similarity threshold

A rejected candidate includes a human-readable explanation.

---

## Safe Final Recommendation

```text
GET /posts/{post_id}/images
```

The endpoint returns the first candidate that clears the guard.

If nothing is safe enough, the API returns:

```text
No confident match.
```

instead of choosing an unrelated image.

---

# Human Review Workflow

The automated mismatch guard and the human review decision are separate.

## Create a suggestion

```text
POST /suggestions
```

## Inspect a suggestion

```text
GET /suggestions/{suggestion_id}
```

## Approve

```text
POST /suggestions/{suggestion_id}/approve
```

## Reject

```text
POST /suggestions/{suggestion_id}/reject
```

Meaning of the two decisions:

- `guard_accepted = true` means the automated safety layer found the image safe enough to present.
- `status = approved` means a human reviewer accepted the suggestion.

A suggestion cannot be reviewed more than once.

---

# Evaluation

The evaluation set contains 10 labeled post/image pairs across:

- Fox
- Wolf
- Dog
- Bear
- Deer

Run:

```bash
python -m scripts.evaluate_matching
```

The script reports:

- Raw Ranking Top-1 Precision
- Final Recommendation Top-1 Precision
- Expected image rank
- Similarity scores
- No-confident-match count
- Active similarity threshold

Results are written to:

```text
data/eval_results.json
```

The precision printed by this script must match the result documented near the top of this README.

---

# Automated Tests

Run:

```bash
python -m pytest -v
```

Current focused test suite:

```text
13 tests
```

Coverage includes:

- AI call-budget enforcement
- Vision schema validation
- Confidence bounds
- Required image attributes
- Cosine similarity behavior
- Vector-dimension mismatch handling
- Correct fox acceptance
- Forced wolf rejection
- Low-confidence candidate rejection

---

# Reliability and Safety

## Low-Confidence Handling

Vision results below:

```text
VISION_CONFIDENCE_THRESHOLD=0.70
```

are flagged rather than silently trusted.

A deliberately degraded fixture produced:

| Field            | Result             |
| ---------------- | ------------------ |
| File             | `ambiguous_02.jpg` |
| Detected subject | `human`            |
| Category         | `person`           |
| Confidence       | `0.60`             |
| Flagged          | `true`             |

The subject classification itself was incorrect, which demonstrates why the confidence guard exists. The system did not treat the output as reliable.

---

## Mismatch Guard

The mismatch guard prevents semantic similarity alone from deciding a recommendation.

For example:

```text
Fox article + wolf image
```

is rejected even when their embeddings are semantically close.

The system also returns a human-readable rejection reason.

---

## No-Match Behavior

If no image clears the safety rules, the system returns:

```text
No confident match.
```

This prevents the application from choosing the nearest image simply because one candidate must rank first mathematically.

---

## AI Call Budget

Before a batch job is created, the application estimates its maximum AI calls as:

```text
total items × maximum attempts
```

If that number exceeds:

```text
AI_MAX_CALLS_PER_JOB
```

the job is rejected before processing begins.

---

# AI Cost Tracking

Vision and embedding calls are recorded in the `ai_cost_logs` table.

Tracked operations include:

- `vision_analysis` using `gemma3:4b`
- `embedding_generation` using `all-minilm`

Both models run locally through Ollama, so the external API cost is currently:

```text
$0
```

Calls are still attributed because cost tracking is part of the reliability design even when the actual monetary cost is zero.

---

# API Reference

| Method | Endpoint                                  | Purpose                             |
| ------ | ----------------------------------------- | ----------------------------------- |
| `GET`  | `/health`                                 | API/database health                 |
| `POST` | `/images`                                 | Add an image                        |
| `GET`  | `/images`                                 | List images                         |
| `POST` | `/posts`                                  | Create a post                       |
| `GET`  | `/posts`                                  | List posts                          |
| `GET`  | `/posts/{post_id}/rank-images`            | Raw semantic ranking                |
| `GET`  | `/posts/{post_id}/check-image/{image_id}` | Inspect mismatch-guard decision     |
| `GET`  | `/posts/{post_id}/images`                 | Get safe final recommendation       |
| `POST` | `/jobs/image-processing`                  | Queue vision processing             |
| `POST` | `/jobs/embedding-generation`              | Queue embedding generation          |
| `GET`  | `/jobs/{job_id}`                          | Inspect job state/progress          |
| `POST` | `/suggestions`                            | Persist a recommendation for review |
| `GET`  | `/suggestions`                            | List suggestions                    |
| `GET`  | `/suggestions/{suggestion_id}`            | Inspect one suggestion              |
| `POST` | `/suggestions/{suggestion_id}/approve`    | Approve a suggestion                |
| `POST` | `/suggestions/{suggestion_id}/reject`     | Reject a suggestion                 |

---

# Expected API Errors

The API uses clean client errors for expected invalid operations:

| Situation                                | Expected status |
| ---------------------------------------- | --------------: |
| Invalid request body                     |           `422` |
| Missing resource                         |           `404` |
| Duplicate post                           |           `409` |
| Duplicate active batch job               |           `409` |
| Reviewing an already reviewed suggestion |           `409` |

---

# Dataset

## Main Corpus

The primary dataset contains 50 animal images across five categories:

| Category | Images |
| -------- | -----: |
| Fox      |     10 |
| Wolf     |     10 |
| Dog      |     10 |
| Bear     |     10 |
| Deer     |     10 |

## Evaluation Set

The labeled evaluation set contains:

| Category  |  Cases |
| --------- | -----: |
| Fox       |      2 |
| Wolf      |      2 |
| Dog       |      2 |
| Bear      |      2 |
| Deer      |      2 |
| **Total** | **10** |

The evaluation labels are stored separately from the metadata sent to the vision model.

---

# Project Structure

```text
app/
├── api/                 # FastAPI routes
├── models/              # SQLAlchemy models
├── schemas/             # Pydantic schemas
└── services/            # Business, AI, matching, review, and guard logic

alembic/                 # Database migrations

data/
├── eval_posts.json      # Labeled evaluation cases
├── eval_results.json    # Evaluation output
├── images_manifest.json # Image source/ground-truth manifest
└── prepared_images/     # Prepared image corpus and robustness fixture

scripts/
├── prepare_images.py
├── seed_images.py
├── create_ambiguous_fixture.py
├── seed_robustness_fixture.py
├── seed_eval_posts.py
├── run_worker.py
└── evaluate_matching.py

tests/
├── test_ai_budget.py
├── test_image_analysis_schema.py
├── test_mismatch_guard.py
└── test_similarity.py

.env.example
BUILDLOG.md
DESIGN.md
EVIDENCE.md
README.md
capstone.yaml
docker-compose.yml
requirements.txt
```

---

# First-Time Demo Flow

For a completely new database, the normal flow is:

```text
1. Start PostgreSQL
2. Run Alembic migrations
3. Seed images and evaluation posts
4. Start FastAPI
5. Start the background worker
6. Queue image processing
7. Wait for image processing to finish
8. Queue embedding generation
9. Wait for embeddings to finish
10. Run the evaluation
11. Test matching and review endpoints
```

Commands:

```bash
docker compose up -d --wait
alembic upgrade head

python -m scripts.seed_images
python -m scripts.create_ambiguous_fixture
python -m scripts.seed_robustness_fixture
python -m scripts.seed_eval_posts
```

Then start the API:

```bash
uvicorn app.main:app --reload
```

In another terminal:

```bash
python -m scripts.run_worker
```

Through Swagger:

```text
POST /jobs/image-processing
```

After that job completes:

```text
POST /jobs/embedding-generation
```

Finally:

```bash
python -m scripts.evaluate_matching
python -m pytest -v
```

---

# Limitations

- The dataset is intentionally small and focused on five animal categories.
- Subject normalization is manually defined for this evaluation domain.
- Cosine similarity is calculated in Python instead of using a dedicated vector database because the dataset is small.
- Model-reported confidence is not perfectly calibrated and can still be overconfident.
- The degraded-image experiment showed that a model may identify the wrong subject even when given explicit confidence instructions.
- Exact-image retrieval is harder than category-level relevance when several images depict similar subjects.
- Ollama and the required models must be installed locally before the system can perform AI operations.
- The project exposes the review workflow through an API rather than a frontend.
- The capstone is designed as a single-system application and does not implement multi-tenant account isolation.

---

# Supporting Documentation

- `DESIGN.md` — architecture and early design decisions
- `BUILDLOG.md` — implementation progress and AI-assisted development notes
- `EVIDENCE.md` — requirement and acceptance-probe evidence
- `capstone.yaml` — evaluator run/seed/test manifest
- `.env.example` — safe environment-variable template

---

## License

MIT
