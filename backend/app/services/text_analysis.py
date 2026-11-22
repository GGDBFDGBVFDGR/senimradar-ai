from typing import Literal

from app.ml.inference import analyze_message
from app.ml.status import text_model_configured
from app.schemas.analysis import TextAnalysisResult, UnavailableAnalysis

LanguageCode = Literal["ru", "kk", "en", "unknown"]


def assess_text(text: str, language: LanguageCode) -> TextAnalysisResult | UnavailableAnalysis:
    """Classify text with the local model. The text is not stored or logged."""

    if not text_model_configured():
        return UnavailableAnalysis(
            status="unavailable",
            code="model_not_configured",
            stage=2,
            input_type="text",
            language=language,
            message="Text fraud analysis model is not configured.",
        )
    try:
        payload = analyze_message(text, language)
    except Exception as exc:
        raise RuntimeError(type(exc).__name__) from None
    return TextAnalysisResult.model_validate(payload)
