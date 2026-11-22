"""Synthetic OCR pages with a known source. These are not user screenshots."""

from __future__ import annotations

import io

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from app.ocr.engine import extract_text
from app.ocr.score import character_error_rate, word_error_rate
from app.ocr.tesseract_ocr import kazakh_ocr_ready

FONT = "/Library/Fonts/Arial Unicode.ttf"
KAZAKH_LETTERS = "ӘәҒғҚқҢңӨөҰұҮүҺһІі"

SAMPLES: list[dict] = [
    {"name": "ru_clean", "text": "Служба банка: срочно переведите деньги на карту", "size": 42, "fill": "white", "ink": "black"},
    {"name": "kk_clean", "text": "Сәлеметсіз бе, шұғыл түрде ақшаны аударыңыз", "size": 42, "fill": "white", "ink": "black"},
    {"name": "kk_letters", "text": "Әә Ғғ Ққ Ңң Өө Ұұ Үү Һһ Іі", "size": 48, "fill": "white", "ink": "black"},
    {"name": "mixed_sms", "text": "Код 482913. Срочно аударыңыз 15000 тенге: https://example.com/pay", "size": 36, "fill": "white", "ink": "black"},
    {"name": "kk_paper", "text": "Құрметті клиент, төлемді өзіңіз растаңыз", "size": 36, "fill": "#f4ecd4", "ink": "black"},
    {"name": "kk_dark", "text": "Бұл хабарлама банктен емес", "size": 36, "fill": "#1e2430", "ink": "white"},
    {"name": "kk_small", "text": "Шұғыл түрде кодты жіберіңіз", "size": 16, "fill": "white", "ink": "black"},
    {"name": "chat", "text": "Сәлем, ақшаны аударыңыз\nЖарайды, ертең кездесеміз", "size": 28, "fill": "#eceff3", "ink": "black", "chat": True},
    {"name": "kk_blur", "text": "Сәлеметсіз бе, ақшаны аударыңыз", "size": 42, "fill": "white", "ink": "black", "blur": 2.2},
]


def render_sample(sample: dict) -> bytes:
    width = 1200
    height = 280 if sample.get("chat") else 180
    image = Image.new("RGB", (width, height), sample["fill"])
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(FONT, sample["size"])
    lines = sample["text"].split("\n")
    if sample.get("chat"):
        y = 28
        for index, line in enumerate(lines):
            bubble = (24, y, 760, y + 64)
            draw.rounded_rectangle(bubble, radius=16, fill="#d9efe4" if index == 0 else "#ffffff")
            draw.text((40, y + 16), line, fill=sample["ink"], font=font)
            y += 84
    else:
        draw.text((28, 58), sample["text"], fill=sample["ink"], font=font)
    if sample.get("blur"):
        image = image.filter(ImageFilter.GaussianBlur(sample["blur"]))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def letter_hits(hypothesis: str) -> list[str]:
    return [char for char in KAZAKH_LETTERS if char in hypothesis]


def measure(engine_language: str) -> list[dict]:
    rows = []
    for sample in SAMPLES:
        if engine_language == "tesseract" and not kazakh_ocr_ready():
            rows.append({"name": sample["name"], "engine": "tesseract", "status": "not_installed"})
            continue
        language = "ru" if engine_language == "vision" else "kk"
        try:
            result = extract_text(render_sample(sample), language)
        except Exception as exc:
            rows.append({"name": sample["name"], "engine": engine_language, "status": getattr(exc, "code", "error")})
            continue
        text = result["text"]
        rows.append(
            {
                "name": sample["name"],
                "engine": result["engine"],
                "status": result["status"],
                "cer": round(character_error_rate(sample["text"], text), 3),
                "wer": round(word_error_rate(sample["text"], text), 3),
                "kazakh_letters_kept": letter_hits(text),
                "ml_language": result["ml_language"],
            }
        )
    return rows
