from typing import Literal

from app.ml.status import text_model_configured
from app.schemas.analysis import UnavailableAnalysis

LanguageCode = Literal["ru", "kk", "en", "unknown"]


def assess_text(language: LanguageCode) -> UnavailableAnalysis:
    """Return an honest refusal. The submitted text is not an argument and is not stored."""

    if text_model_configured():
        return UnavailableAnalysis(
            status="unavailable",
            code="inference_not_implemented",
            stage=2,
            input_type="text",
            language=language,
            message="Text fraud analysis inference is not implemented.",
        )
    return UnavailableAnalysis(
        status="unavailable",
        code="model_not_configured",
        stage=2,
        input_type="text",
        language=language,
        message="Text fraud analysis model is not configured.",
    )
