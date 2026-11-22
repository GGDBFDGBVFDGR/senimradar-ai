import json
import os
from pathlib import Path

import joblib

ARTIFACT_DIR = Path(__file__).resolve().parent / "artifacts"
_CACHE: dict[str, object] = {}


def _active_pointer() -> dict | None:
    pointer = ARTIFACT_DIR / "active_model.json"
    if not pointer.is_file():
        return None
    payload = json.loads(pointer.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return None
    artifact = str(payload.get("artifact", "")).strip()
    card = str(payload.get("card", "")).strip()
    if not artifact or not card or "/" in artifact or "/" in card:
        return None
    return {"artifact": artifact, "card": card}


def model_path() -> Path:
    override = os.environ.get("SENIMRADAR_MODEL_PATH", "").strip()
    if override:
        return Path(override)
    active = _active_pointer()
    if active is not None:
        return ARTIFACT_DIR / active["artifact"]
    return ARTIFACT_DIR / "model.joblib"


def card_path() -> Path:
    override = os.environ.get("SENIMRADAR_MODEL_PATH", "").strip()
    path = model_path()
    if override:
        return path.with_name("model_card.json") if path.name == "model.joblib" else path.with_suffix(".json")
    active = _active_pointer()
    if active is not None:
        return ARTIFACT_DIR / active["card"]
    return ARTIFACT_DIR / "model_card.json"


def reset_runtime() -> None:
    _CACHE.clear()


def text_model_configured() -> bool:
    path = model_path()
    card = card_path()
    return path.is_file() and card.is_file()


def load_runtime() -> dict | None:
    key = str(model_path())
    if _CACHE.get("key") == key and "runtime" in _CACHE:
        return _CACHE["runtime"]  # type: ignore[return-value]
    if not text_model_configured():
        _CACHE.clear()
        _CACHE["key"] = key
        _CACHE["runtime"] = None
        return None
    payload = joblib.load(model_path())
    card = json.loads(card_path().read_text(encoding="utf-8"))
    if payload.get("model_version") != card.get("model_version"):
        raise RuntimeError("model_card_mismatch")
    runtime = {"payload": payload, "card": card}
    _CACHE.clear()
    _CACHE["key"] = key
    _CACHE["runtime"] = runtime
    return runtime
