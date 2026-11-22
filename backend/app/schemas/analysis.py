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
