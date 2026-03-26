# Payment Service

FastAPI + Motor microservice for payment records.

- Database: `payment_db`
- Collection: `payments`
- API prefix: `/api/v1`

## Prerequisites

- Python 3.11+
- MongoDB reachable via `MONGODB_URL`

## Setup

```bash
cd payment-service
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
copy .env.example .env
```

## Run

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8004 --reload
```

Docs: `http://localhost:8004/docs`

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check (`{"status":"ok","service":"payment-service"}`) |
| POST | `/api/v1/payments` | Create payment |
| GET | `/api/v1/payments` | List payments (`limit`, `user_id`, `order_id`, `payment_status`, `payment_method`) |
| GET | `/api/v1/payments/order/{order_id}` | List by order reference |
| GET | `/api/v1/payments/{payment_id}` | Get by MongoDB ObjectId |
| PUT | `/api/v1/payments/{payment_id}/status` | Update payment status |
| DELETE | `/api/v1/payments/{payment_id}` | Delete |

## Conventions

- `payment_id` is MongoDB ObjectId; `order_id` and `user_id` are external references
- UTC timestamps: `created_at`, `updated_at`
- ObjectId in responses serialized as string `id`
- `transaction_reference` is generated server-side on create
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
| `app/utils/` | ObjectId/path/enum/serialization helpers |
