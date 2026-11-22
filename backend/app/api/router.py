from fastapi import APIRouter

from app.api.routes import analysis, health, screenshot, system

router = APIRouter()
router.include_router(health.router)
router.include_router(system.router)
router.include_router(analysis.router)
router.include_router(screenshot.router)
