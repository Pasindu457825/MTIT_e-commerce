"""
Versioned API router (`/api/v1/...`).

Feature routers are composed here so `main.py` only mounts this module once.
"""

from fastapi import APIRouter

from app.routes import cart

router = APIRouter()
router.include_router(cart.router)
