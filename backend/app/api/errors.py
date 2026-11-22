import logging

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    del request
    errors = []
    for error in exc.errors():
        loc = [str(part) for part in error.get("loc", []) if part != "body"]
        errors.append({"loc": loc, "code": str(error.get("type", "invalid"))})
    return JSONResponse(
        status_code=422,
        content={"status": "error", "code": "validation_error", "errors": errors},
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("Unhandled error type=%s path=%s", type(exc).__name__, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"status": "error", "code": "internal_error"},
    )
