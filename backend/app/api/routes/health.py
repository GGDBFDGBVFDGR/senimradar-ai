import logging
from typing import Literal

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app import __version__
from app.core.config import get_settings
from app.db.session import engine
from app.schemas.health import HealthResponse, ReadyResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        version=__version__,
        environment=settings.environment,
    )


@router.get("/health/ready", response_model=ReadyResponse)
def ready() -> ReadyResponse | JSONResponse:
    database: Literal["ok", "unavailable"] = "ok"
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception as exc:
        # Log only the exception type. Database errors can include the connection URL.
        logger.warning("Database readiness check failed: %s", type(exc).__name__)
        database = "unavailable"
    payload = ReadyResponse(
        status="ok" if database == "ok" else "degraded",
        database=database,
    )
    if database != "ok":
        return JSONResponse(status_code=503, content=payload.model_dump())
    return payload
