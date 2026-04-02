# Product Service

FastAPI + Motor microservice for product catalog data.

- Database: `product_db`
- Collection: `products`
- API prefix: `/api/v1`

## Prerequisites

- Python 3.11+
- MongoDB reachable via `MONGODB_URL`

## Setup

```bash
cd product-service
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
copy .env.example .env
```

## Run

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
```

Docs: `http://localhost:8002/docs`

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check (`{"status":"ok","service":"product-service"}`) |
| POST | `/api/v1/products` | Create product |
| GET | `/api/v1/products` | List products (`limit`, `category`, `min_price`, `max_price`) |
| GET | `/api/v1/products/{product_id}` | Get by MongoDB ObjectId |
| PUT | `/api/v1/products/{product_id}` | Partial update |
| DELETE | `/api/v1/products/{product_id}` | Delete |

## Conventions

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
| `app/utils/` | ObjectId/serialization helpers |
