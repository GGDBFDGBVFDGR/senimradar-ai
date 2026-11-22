"""Local screenshot OCR. Images stay in memory and are not logged."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from app.ml.preprocess import looks_kazakh

MAX_SCREENSHOT_BYTES = 8 * 1024 * 1024
OCR_TIMEOUT_SECONDS = 20
MAX_OCR_CHARS = 8000
_BINARY_NAME = "vision_ocr"


class OcrError(Exception):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


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


def extract_text(payload: bytes) -> dict:
    if len(payload) > MAX_SCREENSHOT_BYTES:
        raise OcrError("payload_too_large")
    if image_format(payload) is None:
        raise OcrError("unsupported_type")
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
