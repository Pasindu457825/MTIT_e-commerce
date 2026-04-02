# Review Service

FastAPI + Motor microservice for product reviews.

- Database: `review_db`
- Collection: `reviews`
- API prefix: `/api/v1`

## Prerequisites

- Python 3.11+
- MongoDB reachable via `MONGODB_URL`

## Setup

```bash
cd review-service
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
copy .env.example .env
```

## Run

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8006 --reload
```

Docs: `http://localhost:8006/docs`

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check (`{"status":"ok","service":"review-service"}`) |
| POST | `/api/v1/reviews` | Create review |
| GET | `/api/v1/reviews` | List reviews (`limit`, `product_id`, `user_id`) |
| GET | `/api/v1/reviews/product/{product_id}` | List by product reference |
| GET | `/api/v1/reviews/{review_id}` | Get by MongoDB ObjectId |
| PUT | `/api/v1/reviews/{review_id}` | Partial update |
| DELETE | `/api/v1/reviews/{review_id}` | Delete |

## Conventions

- `review_id` is MongoDB ObjectId; `product_id` and `user_id` are external references
- UTC timestamps: `created_at`, `updated_at`
- ObjectId in responses serialized as string `id`
- MongoDB checked on startup (lifespan ping)
- Shared JSON exception handlers in `app/core/exceptions.py`

## Project Layout

| Path | Role |
|------|------|
| `app/main.py` | App factory, CORS, lifespan, router mounting |
| `app/core/config.py` | Environment-driven settings |
| `app/core/database.py` | Mongo client lifecycle + dependency |
| `app/core/indexes.py` | Service indexes |
| `app/core/exceptions.py` | Shared exception handlers |
| `app/routes/` | `health`, versioned API router, feature routes |
| `app/schemas/` | Request/response models |
| `app/services/` | Business logic layer |
| `app/utils/` | ObjectId/path/serialization helpers |
