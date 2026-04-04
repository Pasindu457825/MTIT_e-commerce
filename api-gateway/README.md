# API Gateway

Lightweight FastAPI gateway that reverse-proxies calls to downstream microservices using `httpx`.

## Features

- One FastAPI gateway service
- Environment-driven downstream service URLs
- Reverse proxy for `/api/v1/{users|products|orders|payments|cart|reviews|notifications}`
- Gateway health endpoint: `GET /health`
- Aggregated downstream health: `GET /health/services`
- Merged Swagger/OpenAPI on the gateway at `GET /docs`
- Timeout handling (`504`) and upstream connection errors (`502`)
- Modular code with comments for learning
- No authentication yet (intentionally)

## Environment

Copy `.env.example` to `.env` in this folder and set URLs as needed:

- `USER_SERVICE_URL`
- `PRODUCT_SERVICE_URL`
- `ORDER_SERVICE_URL`
- `PAYMENT_SERVICE_URL`
- `CART_SERVICE_URL`
- `REVIEW_SERVICE_URL`
- `REQUEST_TIMEOUT_SECONDS` (optional, default `10`)

## Run

```bash
cd api-gateway
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Docs: `http://localhost:8000/docs`

The gateway Swagger UI merges its own documented routes with the OpenAPI schemas exposed by running downstream services. If one downstream service is offline, the docs still load and omit that service.

## Proxy Behavior

Gateway routes are mounted under `/api/v1`:

- `/api/v1/users...` -> user-service
- `/api/v1/products...` -> product-service
- `/api/v1/orders...` -> order-service
- `/api/v1/payments...` -> payment-service
- `/api/v1/cart...` -> cart-service
- `/api/v1/reviews...` -> review-service
- `/api/v1/notifications...` -> notification-service

The gateway preserves method, query string, request body, and most headers.

## Project Layout

| Path | Role |
|------|------|
| `app/main.py` | App factory + shared `httpx.AsyncClient` lifecycle |
| `app/core/config.py` | Environment settings + service URL map |
| `app/routes/proxy.py` | Proxy route handlers under `/api/v1` |
| `app/routes/health.py` | `/health` and `/health/services` |
| `app/services/proxy_service.py` | Upstream forwarding + error mapping |
| `app/services/health_service.py` | Downstream health aggregation |
