from fastapi import APIRouter, File, UploadFile
from fastapi.responses import JSONResponse

from app.core.limits import MAX_SCREENSHOT_BYTES
from app.ocr.engine import OcrError, extract_text
from app.schemas.analysis import ScreenshotOcrResult
from app.schemas.common import ErrorResponse

router = APIRouter(tags=["analysis"])


@router.post(
    "/analysis/screenshot",
    response_model=ScreenshotOcrResult,
    responses={
        408: {"model": ErrorResponse},
        413: {"model": ErrorResponse},
        415: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
    },
)
async def recognize_screenshot(upload: UploadFile = File()) -> JSONResponse:
    """Read text from an image. The file is not stored and the text is not logged."""

    payload = await upload.read(MAX_SCREENSHOT_BYTES + 1)
    await upload.close()
    try:
        result = extract_text(payload)
    except OcrError as exc:
        status = {
            "payload_too_large": 413,
            "unsupported_type": 415,
            "ocr_timeout": 408,
            "ocr_not_available": 503,
        }.get(exc.code, 422)
        return JSONResponse(status_code=status, content={"status": "error", "code": exc.code})
    body = ScreenshotOcrResult.model_validate(result)
    return JSONResponse(status_code=200, content=body.model_dump())
