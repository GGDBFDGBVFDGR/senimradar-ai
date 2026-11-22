from fastapi import APIRouter

from app.api.routes import analysis, health, system

router = APIRouter()
router.include_router(health.router)
router.include_router(system.router)
router.include_router(analysis.router)
