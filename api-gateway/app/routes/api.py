from fastapi import APIRouter

from app.routes import proxy

router = APIRouter()
router.include_router(proxy.router)
