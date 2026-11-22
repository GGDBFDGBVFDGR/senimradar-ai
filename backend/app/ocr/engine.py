"""Local screenshot OCR. Images stay in memory and are not logged."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from app.ml.preprocess import looks_kazakh
from app.ocr.errors import OcrError

MAX_SCREENSHOT_BYTES = 8 * 1024 * 1024
OCR_TIMEOUT_SECONDS = 20
MAX_OCR_CHARS = 8000
_BINARY_NAME = "vision_ocr"


def _source_path() -> Path:
    return Path(__file__).resolve().parent / "vision_ocr.swift"


def _binary_path() -> Path:
    return Path(__file__).resolve().parent / _BINARY_NAME


def ensure_ocr_binary() -> Path:
    source = _source_path()
    binary = _binary_path()
    if binary.is_file() and binary.stat().st_mtime >= source.stat().st_mtime:
        return binary
    if not source.is_file():
        raise OcrError("ocr_not_available")
    try:
        subprocess.run(
            ["swiftc", "-O", "-o", str(binary), str(source)],
            check=True,
            capture_output=True,
            timeout=180,
        )
    except (OSError, subprocess.SubprocessError):
        raise OcrError("ocr_not_available") from None
    return binary


def ocr_available() -> bool:
    try:
        ensure_ocr_binary()
    except OcrError:
        return False
    return True


def image_format(payload: bytes) -> str | None:
    if payload.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if payload.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if len(payload) >= 12 and payload.startswith(b"RIFF") and payload[8:12] == b"WEBP":
        return "webp"
    return None


def extract_text(payload: bytes, language: str = "auto") -> dict:
    if language not in {"auto", "ru", "kk"}:
        raise OcrError("invalid_language")
    if len(payload) > MAX_SCREENSHOT_BYTES:
        raise OcrError("payload_too_large")
    if image_format(payload) is None:
        raise OcrError("unsupported_type")
    if language == "kk":
        return _finish(_read_tesseract(payload), language, "kk", True)
    if language == "ru":
        result = _read_vision(payload)
        ml_language = "ru" if result["text"] else "unconfirmed"
        return _finish(result, language, ml_language, False)
    tesseract_result = _read_tesseract_for_detection(payload)
    if tesseract_result is not None and looks_kazakh(tesseract_result["text"]):
        tesseract_result["warnings"].append("kazakh_script_detected")
        return _finish(tesseract_result, "auto", "kk", True)
    vision = _read_vision(payload)
    if tesseract_result is None:
        vision["warnings"].append("language_unconfirmed")
        return _finish(vision, "auto", "unconfirmed", False)
    vision["warnings"].append("language_checked")
    ml_language = "ru" if vision["text"] else "unconfirmed"
    return _finish(vision, "auto", ml_language, False)


def _read_tesseract(payload: bytes) -> dict:
    from app.ocr.tesseract_ocr import read_tesseract

    return read_tesseract(payload)


def _read_tesseract_for_detection(payload: bytes) -> dict | None:
    from app.ocr.tesseract_ocr import kazakh_ocr_ready

    if not kazakh_ocr_ready():
        return None
    try:
        return _read_tesseract(payload)
    except OcrError:
        return None


def _finish(result: dict, selected_language: str, ml_language: str, language_locked: bool) -> dict:
    if looks_kazakh(result["text"]):
        ml_language = "kk"
        language_locked = True
        if "kazakh_glyphs_detected" not in result["warnings"]:
            result["warnings"].append("kazakh_glyphs_detected")
    result["selected_language"] = selected_language
    result["ml_language"] = ml_language
    result["language_locked"] = language_locked
    return result


def _read_vision(payload: bytes) -> dict:
    binary = ensure_ocr_binary()
    try:
        completed = subprocess.run(
            [str(binary)],
            input=payload,
            capture_output=True,
            timeout=OCR_TIMEOUT_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired:
        raise OcrError("ocr_timeout") from None
    except OSError:
        raise OcrError("ocr_not_available") from None
    if completed.returncode != 0 or not completed.stdout:
        raise OcrError("unreadable")
    try:
        parsed = json.loads(completed.stdout)
    except json.JSONDecodeError:
        raise OcrError("unreadable") from None
    status = parsed.get("status")
    warnings = [item for item in parsed.get("warnings", []) if isinstance(item, str)]
    if status == "error":
        code = warnings[0] if warnings else "unreadable"
        raise OcrError(code if code in {"unreadable", "too_many_pixels"} else "unreadable")
    text = parsed.get("text") if isinstance(parsed.get("text"), str) else ""
    text = text.replace("\x00", "").strip()
    if len(text) > MAX_OCR_CHARS:
        text = text[:MAX_OCR_CHARS].rstrip()
        warnings.append("text_truncated")
    if "kazakh_ocr_unsupported" not in warnings:
        warnings.append("kazakh_ocr_unsupported")
    if looks_kazakh(text) and "kazakh_glyphs_detected" not in warnings:
        warnings.append("kazakh_glyphs_detected")
    if status not in {"ok", "no_text"}:
        raise OcrError("unreadable")
    return {
        "status": "no_text" if not text else "ok",
        "text": text,
        "engine": "apple_vision",
        "warnings": warnings,
        "line_count": int(parsed.get("lineCount") or 0) if text else 0,
    }
