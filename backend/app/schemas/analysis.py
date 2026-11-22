from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.core.limits import MAX_TEXT_LENGTH


class TextAnalysisRequest(BaseModel):
    model_config = {"extra": "forbid"}

    text: str = Field(min_length=1, max_length=MAX_TEXT_LENGTH)
    language: Literal["ru", "kk", "en", "unknown"] = "unknown"

    @field_validator("text")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("blank")
        if "\x00" in stripped:
            raise ValueError("invalid_character")
        if len(stripped) > MAX_TEXT_LENGTH:
            raise ValueError("too_long")
        return stripped


class ScreenshotOcrResult(BaseModel):
    status: Literal["ok", "no_text"]
    text: str
    engine: Literal["apple_vision"]
    warnings: list[str]
    line_count: int


class UnavailableAnalysis(BaseModel):
    status: Literal["unavailable"]
    code: Literal["model_not_configured", "inference_not_implemented"]
    stage: int
    input_type: Literal["text"]
    language: Literal["ru", "kk", "en", "unknown"]
    message: str
    model_version: None = None
    risk_level: None = None
    risk_score: None = None


class TextAnalysisResult(BaseModel):
    status: Literal["ok", "insufficient"]
    input_type: Literal["text"] = "text"
    language: Literal["ru", "kk", "en", "unknown"]
    language_evaluation: Literal["evaluated", "not_evaluated", "not_confirmed"]
    model_version: str
    risk_level: Literal["low", "medium", "high", "unknown"]
    risk_score: None = None
    confidence_calibrated: bool
    uncertain: bool
    indicators: list[str]
    cues: list[str]
    recommendations: list[str]
    limitations: list[str]
