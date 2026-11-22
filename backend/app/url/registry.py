"""Separate from the message-model registry. Loading this does not change the text model."""

from __future__ import annotations

import json
from pathlib import Path

import joblib

ARTIFACT_DIR = Path(__file__).resolve().parents[1] / "ml" / "artifacts"
_CACHE: dict[str, object] = {}


def pointer_path() -> Path:
    return ARTIFACT_DIR / "active_url_model.json"


def url_model_configured() -> bool:
    pointer = pointer_path()
    if not pointer.is_file():
        return False
    payload = json.loads(pointer.read_text(encoding="utf-8"))
    artifact = ARTIFACT_DIR / str(payload.get("artifact", ""))
    card = ARTIFACT_DIR / str(payload.get("card", ""))
    return artifact.is_file() and card.is_file() and "/" not in str(payload.get("artifact", ""))


def load_url_runtime() -> dict | None:
    if _CACHE.get("ready") is True:
        return _CACHE["runtime"]  # type: ignore[return-value]
    if not url_model_configured():
        _CACHE.clear()
        _CACHE["ready"] = True
        _CACHE["runtime"] = None
        return None
    pointer = json.loads(pointer_path().read_text(encoding="utf-8"))
    payload = joblib.load(ARTIFACT_DIR / pointer["artifact"])
    card = json.loads((ARTIFACT_DIR / pointer["card"]).read_text(encoding="utf-8"))
    if payload.get("model_version") != card.get("model_version"):
        raise RuntimeError("url_model_card_mismatch")
    runtime = {"payload": payload, "card": card}
    _CACHE.clear()
    _CACHE["ready"] = True
    _CACHE["runtime"] = runtime
    return runtime


def reset_url_runtime() -> None:
    _CACHE.clear()
