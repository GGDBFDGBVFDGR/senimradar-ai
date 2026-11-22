from fastapi import APIRouter

from app.ml.status import text_model_configured
from app.ocr.engine import ocr_available
from app.ocr.tesseract_ocr import kazakh_ocr_ready
from app.schemas.system import CapabilitiesResponse, Capability

router = APIRouter(tags=["system"])


@router.get("/system/capabilities", response_model=CapabilitiesResponse)
def capabilities() -> CapabilitiesResponse:
    model_configured = text_model_configured()
    screenshot_ready = ocr_available()
    return CapabilitiesResponse(
        product="SenimRadar AI",
        stage=3,
        model_configured=model_configured,
        third_party_ai_enabled=False,
        supported_locales=["ru", "kk"],
        capabilities=[
            Capability(
                key="text_analysis",
                status="ready" if model_configured else "unavailable",
                stage=2,
                note_code="model_ready" if model_configured else "model_not_configured",
            ),
            Capability(
                key="screenshot_analysis",
                status="ready" if screenshot_ready else "unavailable",
                stage=3,
                note_code=("ocr_kazakh" if kazakh_ocr_ready() else "ocr_local") if screenshot_ready else "ocr_not_available",
            ),
            Capability(
                key="url_analysis",
                status="planned",
                stage=4,
                note_code="scheduled_stage",
            ),
            Capability(
                key="voice_analysis",
                status="planned",
                stage=6,
                note_code="scheduled_stage",
            ),
            Capability(
                key="history",
                status="disabled",
                stage=7,
                note_code="consent_required",
            ),
            Capability(
                key="insights",
                status="unavailable",
                stage=5,
                note_code="requires_real_records",
            ),
        ],
    )
