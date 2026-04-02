# Local Developer Setup Guide

This guide helps you run all services locally on the recommended ports.

## Python Version

- Recommended: **Python 3.12**
- Minimum supported in docs: **Python 3.11+**

Using one Python version across all services avoids dependency mismatch issues.

## Services and Ports

| Service | Port |
|---|---:|
| api-gateway | 8000 |
| user-service | 8001 |
| product-service | 8002 |
| order-service | 8003 |
| payment-service | 8004 |
| cart-service | 8005 |
| review-service | 8006 |

---

## 1) Create virtual environments and install dependencies

You can use one venv per service (recommended for isolation) or one shared venv.

### Windows PowerShell (per service)

```powershell
# user-service
cd user-service
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cd ..

# product-service
cd product-service
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cd ..

# order-service
cd order-service
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cd ..

# payment-service
cd payment-service
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cd ..

# cart-service
cd cart-service
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cd ..

# review-service
cd review-service
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cd ..

# api-gateway
cd api-gateway
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cd ..
```

---

## 2) Create `.env` files for each service

Copy each `.env.example` to `.env` in the same folder:

```powershell
copy api-gateway\.env.example api-gateway\.env
copy user-service\.env.example user-service\.env
copy product-service\.env.example product-service\.env
copy order-service\.env.example order-service\.env
copy payment-service\.env.example payment-service\.env
copy cart-service\.env.example cart-service\.env
copy review-service\.env.example review-service\.env
```

### What to set

- For all domain services (`user/product/order/payment/cart/review`):
  - `APP_NAME`, `APP_HOST`, `APP_PORT`
  - `MONGODB_URL`
  - `DATABASE_NAME`
- For gateway:
  - `APP_NAME`, `APP_HOST`, `APP_PORT`
  - `USER_SERVICE_URL`, `PRODUCT_SERVICE_URL`, `ORDER_SERVICE_URL`, `PAYMENT_SERVICE_URL`, `CART_SERVICE_URL`, `REVIEW_SERVICE_URL`
  - Optional: `REQUEST_TIMEOUT_SECONDS`

Make sure each service `APP_PORT` matches the table above.

---

## 3) Run all services (one terminal per service)

> Open 7 terminals. In each terminal, activate that service venv first.

### user-service (8001)
```powershell
cd user-service
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

### product-service (8002)
```powershell
cd product-service
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
```

### order-service (8003)
```powershell
cd order-service
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --host 0.0.0.0 --port 8003 --reload
```

### payment-service (8004)
```powershell
cd payment-service
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --host 0.0.0.0 --port 8004 --reload
```

### cart-service (8005)
```powershell
cd cart-service
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --host 0.0.0.0 --port 8005 --reload
```

### review-service (8006)
```powershell
cd review-service
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --host 0.0.0.0 --port 8006 --reload
```

### api-gateway (8000)
```powershell
cd api-gateway
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 4) Verify with Swagger and health endpoints

### Swagger UIs

- Gateway: `http://localhost:8000/docs`
- User: `http://localhost:8001/docs`
- Product: `http://localhost:8002/docs`
- Order: `http://localhost:8003/docs`
- Payment: `http://localhost:8004/docs`
- Cart: `http://localhost:8005/docs`
- Review: `http://localhost:8006/docs`

Gateway helper redirects (for demos):

- `http://localhost:8000/docs/users`
- `http://localhost:8000/docs/products`
- `http://localhost:8000/docs/orders`
- `http://localhost:8000/docs/payments`
- `http://localhost:8000/docs/cart`
- `http://localhost:8000/docs/reviews`

### Health checks

- Gateway: `http://localhost:8000/health`
- Gateway aggregated services: `http://localhost:8000/health/services`
- User: `http://localhost:8001/health`
- Product: `http://localhost:8002/health`
- Order: `http://localhost:8003/health`
- Payment: `http://localhost:8004/health`
- Cart: `http://localhost:8005/health`
- Review: `http://localhost:8006/health`

If `/health/services` shows `degraded`, check that the corresponding downstream service is running and that its URL in `api-gateway/.env` is correct.
