# Order Service

FastAPI + Motor microservice for orders.

- Database: `order_db`
- Collection: `orders`
- API prefix: `/api/v1`

## Prerequisites

- Python 3.11+
- MongoDB reachable via `MONGODB_URL`

## Setup

```bash
cd order-service
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
copy .env.example .env
```

## Run

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8003 --reload
```

Docs: `http://localhost:8003/docs`

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check (`{"status":"ok","service":"order-service"}`) |
| POST | `/api/v1/orders` | Create order |
| GET | `/api/v1/orders` | List orders (`limit`, `user_id`, `status`) |
| GET | `/api/v1/orders/user/{user_id}` | List by user reference |
| GET | `/api/v1/orders/{order_id}` | Get by MongoDB ObjectId |
| PUT | `/api/v1/orders/{order_id}/status` | Update order status |
| DELETE | `/api/v1/orders/{order_id}` | Delete |

## Conventions

- `order_id` is MongoDB ObjectId; `user_id` and item `product_id` are external references
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
| `app/utils/` | ObjectId/path/status/serialization helpers |
