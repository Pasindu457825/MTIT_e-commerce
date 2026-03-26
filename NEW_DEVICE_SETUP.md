# New Device Setup Guide

Use this guide when setting up the project on a new laptop/PC.

## 1) Install prerequisites

- Python **3.12** recommended (3.11+ works)
- Git
- MongoDB (local) or MongoDB Atlas access
- (Optional) VS Code / Cursor

## 2) Clone the repository

```bash
git clone <your-repo-url>
cd MTIT_e-commerce
```

## 3) Create `.env` files

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

## 4) Create virtual environments and install dependencies

Run the following once per service:

```powershell
cd user-service
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cd ..

cd product-service
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cd ..

cd order-service
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cd ..

cd payment-service
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cd ..

cd cart-service
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cd ..

cd review-service
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cd ..

cd api-gateway
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cd ..
```

## 5) Start all services (7 terminals)

Open one terminal per service and run:

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

## 6) Verify setup

### Health checks

- Gateway: `http://localhost:8000/health`
- Gateway downstream summary: `http://localhost:8000/health/services`
- User: `http://localhost:8001/health`
- Product: `http://localhost:8002/health`
- Order: `http://localhost:8003/health`
- Payment: `http://localhost:8004/health`
- Cart: `http://localhost:8005/health`
- Review: `http://localhost:8006/health`

### Swagger docs

- Gateway: `http://localhost:8000/docs`
- User: `http://localhost:8001/docs`
- Product: `http://localhost:8002/docs`
- Order: `http://localhost:8003/docs`
- Payment: `http://localhost:8004/docs`
- Cart: `http://localhost:8005/docs`
- Review: `http://localhost:8006/docs`

### Gateway doc shortcuts

- `http://localhost:8000/docs/users`
- `http://localhost:8000/docs/products`
- `http://localhost:8000/docs/orders`
- `http://localhost:8000/docs/payments`
- `http://localhost:8000/docs/cart`
- `http://localhost:8000/docs/reviews`

## 7) Run tests (optional)

Install test dependency once at repo root:

```powershell
pip install -r requirements-test.txt
```

Run any service tests:

```powershell
cd user-service
python -m pytest -q
```

(Repeat for other services/gateway.)
