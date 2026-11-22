from typing import Literal

from pydantic import BaseModel, Field


class Capability(BaseModel):
    key: str
    status: Literal["ready", "unavailable", "planned", "disabled"]
    stage: int
    note_code: str


class CapabilitiesResponse(BaseModel):
    product: str
    stage: int = Field(description="Current implemented product stage.")
    model_configured: bool
    third_party_ai_enabled: bool
    supported_locales: list[Literal["ru", "kk"]]
    capabilities: list[Capability]
