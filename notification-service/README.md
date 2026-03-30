# Notification Service

FastAPI + Motor microservice for user notifications.

- Database: `notification_db`
- Collection: `notifications`
- API prefix: `/api/v1`

## Prerequisites

- Python 3.11+
- MongoDB reachable via `MONGODB_URL`

## Setup

```bash
cd notification-service
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
copy .env.example .env
```

## Run

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8007 --reload
```

Docs: `http://localhost:8007/docs`

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check (`{"status":"ok","service":"notification-service"}`) |
| POST | `/api/v1/notifications` | Create notification |
| GET | `/api/v1/notifications` | List notifications (`limit`, `user_id`, `is_read`) |
| GET | `/api/v1/notifications/user/{user_id}` | List by user reference (`is_read` filter) |
| GET | `/api/v1/notifications/{notification_id}` | Get by MongoDB ObjectId |
| PUT | `/api/v1/notifications/{notification_id}` | Partial update (title, message) |
| PATCH | `/api/v1/notifications/{notification_id}/read` | Mark single notification as read |
| PATCH | `/api/v1/notifications/user/{user_id}/read-all` | Mark all user notifications as read |
| DELETE | `/api/v1/notifications/{notification_id}` | Delete |

## Notification Types

| Type | Description |
|------|-------------|
| `order_placed` | A new order was placed |
| `order_confirmed` | Order has been confirmed |
| `order_shipped` | Order has been shipped |
| `order_delivered` | Order has been delivered |
| `order_cancelled` | Order was cancelled |
| `payment_confirmed` | Payment was successful |
| `payment_failed` | Payment failed |
| `review_posted` | A review was posted |
| `general` | General purpose notification |

## Conventions

- `notification_id` is MongoDB ObjectId; `user_id` is an external reference (plain string)
- UTC timestamps: `created_at`, `updated_at`
- `is_read` defaults to `false` on creation
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
