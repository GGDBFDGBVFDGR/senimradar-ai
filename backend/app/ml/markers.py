"""Structural markers for Stage 2.1 models.

These are general instruction shapes, not exceptions for individual sentences.
They are appended only when a model card sets structural_markers=true.
The Stage 2 artifact does not set that flag, so its input stays unchanged.
"""

import re

_PROHIBITION_RE = re.compile(
    r"не\s+(?:сообща|называ|говори|передава|переводи|вводи|отправ|переход)|"
    r"никому\s+не|"
    r"ешкімге|"
    r"айтпаңыз|жібермеңіз|аудармаңыз|енгізбеңіз|баспаңыз",
    re.IGNORECASE,
)
_DIRECT_REQUEST_RE = re.compile(
    r"\b(?:сообщите|пришлите|назовите|переведите|введите|отправьте|перейдите|"
    r"жіберіңіз|айтыңыз|енгізіңіз|аударыңыз)\b",
    re.IGNORECASE,
)


def prohibition_only(text: str) -> bool:
    """True when the text forbids an action and does not also demand one."""

    return _PROHIBITION_RE.search(text) is not None and _DIRECT_REQUEST_RE.search(text) is None


def structural_markers(text: str) -> str:
    prohibition = _PROHIBITION_RE.search(text) is not None
    request = _DIRECT_REQUEST_RE.search(text) is not None
    parts: list[str] = []
    if prohibition:
        parts.append("marker_prohibition")
    if request:
        parts.append("marker_request")
    if prohibition and not request:
        parts.append("marker_warning_only")
    if prohibition and request:
        parts.append("marker_mixed_instruction")
    return " ".join(parts)


def model_input(text: str, structural: bool) -> str:
    from app.ml.preprocess import preprocess_text

    prepared = preprocess_text(text)
    if not structural:
        return prepared
    extra = structural_markers(text)
    if not extra:
        return prepared
    return f"{prepared} {extra}"
