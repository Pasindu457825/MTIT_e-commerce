# MTIT E-Commerce — Microservices (FastAPI)

This repository is a **production-oriented** Python microservices layout for an e-commerce platform. Each bounded context runs as an independent **FastAPI** service with its own configuration, persistence boundary, and deployment unit.

Developer quickstart: see `DEVELOPER_SETUP.md` for running all services locally.

## Architecture

```text
                    ┌─────────────────┐
   Clients ────────►│   API Gateway   │
                    │   (routing)     │
                    └────────┬────────┘
                             │
     ┌───────────┬───────────┼───────────┬───────────┬───────────┐
     ▼           ▼           ▼           ▼           ▼           ▼
┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
│  User   │ │ Product │ │  Order  │ │ Payment │ │  Cart   │ │ Review  │
│ Service │ │ Service │ │ Service │ │ Service │ │ Service │ │ Service │
└─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘
```

### Responsibilities

| Service | Role |
|--------|------|
| **api-gateway** | Single entry point for clients. Forwards requests to downstream services using configured base URLs. Add auth, rate limiting, and aggregation here as the system grows. |
| **user-service** | Accounts, profiles, authentication-related data (extend as needed). |
| **product-service** | Catalog, inventory references, product metadata. |
| **order-service** | Order lifecycle and orchestration touchpoints with other services. |
| **payment-service** | Payment intents, provider webhooks, reconciliation (stubs today). |
| **cart-service** | Session or user carts before checkout. |
| **review-service** | Product reviews and ratings. |

### Domain services (user, product, order, payment, cart, review)

The six domain microservices share the **same architecture**:

- **FastAPI** with **async** I/O and **Motor** (async MongoDB driver; `pymongo` types/errors are used where the stack exposes them).
- **Configuration** from `.env` via `pydantic-settings` (`app/core/config.py`).
- **CORS** middleware (defaults in code; you can extend `app/core/config.py` to read extra keys from `.env` if needed).
- **`GET /health`** on each service (outside the versioned API).
- **Versioned API prefix** `/api/v1` — mount feature routers under `app/routes/api.py` when you implement them.
- **Startup validation**: MongoDB **ping** in the app lifespan; the process exits on startup if the cluster is unreachable.
- **Exception handlers** for validation errors, MongoDB errors, `HTTPException`, and a safe generic 500.

Business REST endpoints are **not** implemented yet; only the shell and `/health` are live.

### Per-service layout

Each domain service follows the same module boundaries:

- `app/main.py` — Application factory, CORS, lifespan (Mongo connect/ping/disconnect), exception registration.
- `app/core/config.py` — Settings from environment / `.env`.
- `app/core/database.py` — Motor client lifecycle and `get_database` dependency.
- `app/core/exceptions.py` — JSON exception handlers.
- `app/models/` — Document shapes / helpers for MongoDB collections.
- `app/schemas/` — Pydantic request/response models (for future endpoints).
- `app/routes/` — HTTP routers (`health.py`, `api.py` placeholder).
- `app/services/` — Domain logic (for future use cases).
- `app/utils/` — Shared helpers (ids, time, hashing, etc.).

### Default ports (local development)

| Service | Port |
|---------|------|
| api-gateway | 8000 |
| user-service | 8001 |
| product-service | 8002 |
| order-service | 8003 |
| payment-service | 8004 |
| cart-service | 8005 |
| review-service | 8006 |

### Where to put `.env` files

Each service loads configuration from a **`.env` file in that service’s own directory** (the folder that contains `requirements.txt` and `app/`), when you run Uvicorn with that directory as the working directory.

1. Copy `service-name/.env.example` to **`service-name/.env`** (same folder as the example).
2. Edit **`.env`** with your real host, port, and MongoDB settings. **Do not commit `.env`** — it may later hold passwords or private connection strings. The committed **`.env.example`** files contain **placeholders only**.

### Running locally

1. Create a virtual environment per service (or one repo-wide venv) and install dependencies:

   ```bash
   cd user-service
   pip install -r requirements.txt
   ```

2. Start **MongoDB** (local or Atlas). Copy `.env.example` to `.env` and set `MONGODB_URL` and `DATABASE_NAME` (and `APP_*` if you change bind address or port).

3. Start the app (example — **user-service**). Host and port should match `APP_HOST` and `APP_PORT` in `.env`:

   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
   ```

Start downstream services before the gateway if you use proxy routes. The gateway reads upstream base URLs from its environment.

**Gateway proxy:** `GET|POST|… /api/v1/{service_key}/{downstream_path}` forwards to `{SERVICE_URL}/api/v1/{service_key}/{downstream_path}`. Keys: `users`, `products`, `orders`, `payments`, `cart`, `reviews`. Example: `GET http://localhost:8000/api/v1/users` → user-service `GET http://localhost:8001/api/v1/users`. Until you add routers under each service’s `/api/v1`, proxied paths may return **404**.

**api-gateway** is separate from the six domain services: it proxies HTTP to them and uses its own dependencies (see `api-gateway/README.md`); it is **not** on the Motor/Mongo stack used by the domain services.

### What is intentionally out of scope here

- **Docker / Kubernetes** — not included yet; add when you are ready to package and orchestrate.
- **MongoDB schema governance** — add conventions or tools (e.g. indexes, validation rules) as collections evolve.
- **Message buses & sagas** — order/payment flows often use async events; folders are structured so you can add clients and workers without reshaping the app.

## Repository structure

```text
api-gateway/
user-service/
product-service/
order-service/
payment-service/
cart-service/
review-service/
README.md   (this file)
```

Each folder is a standalone Python package with its own `requirements.txt`, `.env.example`, and `README.md`.
