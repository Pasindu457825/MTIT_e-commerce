"""
Versioned API router (`/api/v1/...`).

Feature routers are composed here so `main.py` only mounts this module once.
"""

from fastapi import APIRouter

from app.routes import auth, users

router = APIRouter()
router.include_router(auth.router)
router.include_router(users.router)
