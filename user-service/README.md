# User Service

FastAPI + Motor microservice for user records.

- Database: `user_db`
- Collection: `users`
- API prefix: `/api/v1`

## Prerequisites

- Python 3.11+
- MongoDB reachable via `MONGODB_URL`

## Setup

```bash
cd user-service
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
copy .env.example .env
```

## Run

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

Docs: `http://localhost:8001/docs`

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check (`{"status":"ok","service":"user-service"}`) |
| POST | `/api/v1/auth/register` | Register user (`role`: `user` or `admin`) and return bearer token |
| POST | `/api/v1/auth/login` | Login with email/password and return bearer token |
| GET | `/api/v1/auth/me` | Get current user from bearer token |
| GET | `/api/v1/users/me` | Get my profile (logged-in user) |
| POST | `/api/v1/users` | Create user (requires `password` in payload) |
| GET | `/api/v1/users` | List users (`limit`) with optional `search` |
| GET | `/api/v1/users/{user_id}` | Get by MongoDB ObjectId |
| PUT | `/api/v1/users/{user_id}` | Partial update |
| DELETE | `/api/v1/users/{user_id}` | Delete |

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
