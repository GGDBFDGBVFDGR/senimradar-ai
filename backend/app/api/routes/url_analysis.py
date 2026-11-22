from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.schemas.analysis import UrlAnalysisRequest, UrlAnalysisResult, UrlUnavailable
from app.schemas.common import ErrorResponse
from app.url.inference import analyze_url

router = APIRouter(tags=["analysis"])


@router.post(
    "/analysis/url",
    response_model=UrlAnalysisResult | UrlUnavailable,
    responses={422: {"model": ErrorResponse}, 503: {"model": UrlUnavailable}},
)
def analyze_submitted_url(payload: UrlAnalysisRequest) -> JSONResponse:
    try:
        result = analyze_url(payload.url)
    except RuntimeError as exc:
        if str(exc) != "url_model_missing":
            raise RuntimeError(type(exc).__name__) from None
        body = UrlUnavailable(
            status="unavailable",
            code="model_not_configured",
            stage=4,
            message="URL model is not configured.",
        )
        return JSONResponse(status_code=503, content=body.model_dump())
    except Exception as exc:
        raise RuntimeError(type(exc).__name__) from None
    return JSONResponse(status_code=200, content=UrlAnalysisResult.model_validate(result).model_dump())
