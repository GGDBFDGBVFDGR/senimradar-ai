from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.schemas.analysis import TextAnalysisRequest, TextAnalysisResult, UnavailableAnalysis
from app.schemas.common import ErrorResponse
from app.services.text_analysis import assess_text

router = APIRouter(tags=["analysis"])


@router.post(
    "/analysis/text",
    response_model=TextAnalysisResult | UnavailableAnalysis,
    responses={
        422: {"model": ErrorResponse},
        413: {"model": ErrorResponse},
        429: {"model": ErrorResponse},
        503: {"model": UnavailableAnalysis},
    },
)
def analyze_text(payload: TextAnalysisRequest) -> JSONResponse:
    result = assess_text(payload.text, payload.language)
    status_code = 503 if isinstance(result, UnavailableAnalysis) else 200
    return JSONResponse(status_code=status_code, content=result.model_dump())
