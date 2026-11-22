from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.schemas.analysis import TextAnalysisRequest, UnavailableAnalysis
from app.schemas.common import ErrorResponse
from app.services.text_analysis import assess_text

router = APIRouter(tags=["analysis"])


@router.post(
    "/analysis/text",
    status_code=503,
    response_model=UnavailableAnalysis,
    responses={
        422: {"model": ErrorResponse},
        413: {"model": ErrorResponse},
        429: {"model": ErrorResponse},
    },
)
def analyze_text(payload: TextAnalysisRequest) -> JSONResponse:
    # The body is validated by Pydantic and then discarded. Only the language
    # code is echoed, because a model prediction does not exist yet.
    refusal = assess_text(payload.language)
    return JSONResponse(status_code=503, content=refusal.model_dump())
