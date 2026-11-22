"""Optional local Tesseract reader for Kazakh and Russian text.

The binary and traineddata files are not downloaded by the application.
"""

from __future__ import annotations

import io
import shutil
import subprocess

from PIL import Image, ImageOps, UnidentifiedImageError

from app.ocr.errors import OcrError

OCR_TIMEOUT_SECONDS = 20
MAX_SIDE = 8000
MAX_PIXELS = 12_000_000
LOW_CONFIDENCE = 60.0


def tesseract_binary() -> str | None:
    return shutil.which("tesseract")


def kazakh_ocr_ready() -> bool:
    return tesseract_binary() is not None and _languages_ready()


def _languages_ready() -> bool:
    binary = tesseract_binary()
    if binary is None:
        return False
    try:
        completed = subprocess.run(
            [binary, "--list-langs"],
            capture_output=True,
            timeout=10,
            check=False,
            text=True,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    names = set((completed.stdout + completed.stderr).split())
    return "kaz" in names and "rus" in names


def read_tesseract(payload: bytes) -> dict:
    binary = tesseract_binary()
    if binary is None or not _languages_ready():
        raise OcrError("kazakh_ocr_unavailable")
    image_bytes = _sanitize_image(payload)
    try:
        completed = subprocess.run(
            [binary, "stdin", "stdout", "-l", "kaz+rus", "--psm", "6", "tsv"],
            input=image_bytes,
            capture_output=True,
            timeout=OCR_TIMEOUT_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired:
        raise OcrError("ocr_timeout") from None
    except OSError:
        raise OcrError("kazakh_ocr_unavailable") from None
    if completed.returncode != 0 or not completed.stdout:
        raise OcrError("unreadable")
    text, mean_confidence = _text_from_tsv(completed.stdout.decode("utf-8", errors="replace"))
    warnings: list[str] = []
    if mean_confidence is not None and mean_confidence < LOW_CONFIDENCE:
        warnings.append("low_ocr_confidence")
    return {
        "status": "no_text" if not text else "ok",
        "text": text,
        "engine": "tesseract",
        "warnings": warnings,
        "line_count": 0 if not text else text.count("\n") + 1,
    }


def _sanitize_image(payload: bytes) -> bytes:
    Image.MAX_IMAGE_PIXELS = MAX_PIXELS
    try:
        with Image.open(io.BytesIO(payload)) as image:
            image.load()
            width, height = image.size
            if width <= 0 or height <= 0 or width > MAX_SIDE or height > MAX_SIDE or width * height > MAX_PIXELS:
                raise OcrError("too_many_pixels")
            oriented = ImageOps.exif_transpose(image)
            if oriented.mode not in {"RGB", "L"}:
                oriented = oriented.convert("RGB")
            buffer = io.BytesIO()
            oriented.save(buffer, format="PNG")
            return buffer.getvalue()
    except OcrError:
        raise
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
        raise OcrError("unreadable") from None


def _text_from_tsv(raw: str) -> tuple[str, float | None]:
    grouped: list[str] = []
    current_key: tuple[str, str, str, str] | None = None
    current_words: list[str] = []
    confidences: list[float] = []
    for row in raw.splitlines()[1:]:
        parts = row.split("\t")
        if len(parts) < 12 or parts[0] != "5":
            continue
        word = parts[11].strip()
        if not word:
            continue
        key = (parts[1], parts[2], parts[3], parts[4])
        if key != current_key:
            if current_words:
                grouped.append(" ".join(current_words))
            current_key = key
            current_words = [word]
        else:
            current_words.append(word)
        try:
            confidence = float(parts[10])
        except ValueError:
            confidence = -1
        if confidence >= 0:
            confidences.append(confidence)
    if current_words:
        grouped.append(" ".join(current_words))
    text = "\n".join(grouped).strip()
    mean = sum(confidences) / len(confidences) if confidences else None
    return text, mean
