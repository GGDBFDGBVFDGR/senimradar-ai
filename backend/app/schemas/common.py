from typing import Literal

from pydantic import BaseModel


class ErrorDetail(BaseModel):
    loc: list[str]
    code: str


class ErrorResponse(BaseModel):
    status: Literal["error"]
    code: str
    errors: list[ErrorDetail] | None = None
