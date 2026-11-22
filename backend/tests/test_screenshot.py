import io

from PIL import Image, ImageDraw, ImageFilter, ImageFont
from PIL.PngImagePlugin import PngInfo

from app.ml.indicators import detect_indicators
from app.ml.inference import analyze_message
from app.ocr.engine import image_format

FONT = "/Library/Fonts/Arial Unicode.ttf"


def _png(lines: list[str], size: tuple[int, int] = (1100, 520), blur: float = 0) -> bytes:
    image = Image.new("RGB", size, "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(FONT, 42)
    y = 48
    for line in lines:
        draw.text((36, y), line, fill=(0, 0, 0), font=font)
        y += 72
    if blur:
        image = image.filter(ImageFilter.GaussianBlur(blur))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _post(client, payload: bytes, name: str = "shot.png", content_type: str = "image/png", language: str = "auto"):
    return client.post(
        "/api/v1/analysis/screenshot",
        files={"upload": (name, payload, content_type)},
        data={"language": language},
    )


def test_image_format_uses_bytes_not_the_name():
    assert image_format(b"\x89PNG\r\n\x1a\nrest") == "png"
    assert image_format(b"\xff\xd8\xffrest") == "jpeg"
    assert image_format(b"RIFF0000WEBP") == "webp"
    assert image_format(b"GIF89a") is None


def test_receipt_words_are_not_called_a_payment_request():
    assert "payment_request" not in detect_indicators("Оплата прошла, перевод не нужен.")


def test_password_denial_is_not_called_a_password_request():
    assert "password_request" not in detect_indicators("Это не пароль банка, ничего отправлять не нужно.")


def test_kept_code_warning_is_not_a_request():
    indicators = detect_indicators("Код из SMS оставляйте при себе.")
    assert "fraud_warning" in indicators
    assert "otp_request" not in indicators


def test_russian_scam_text_is_read_and_classified_separately(client):
    source = "Служба банка: срочно переведите деньги на карту"
    response = _post(client, _png([source]))
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["engine"] == "apple_vision"
    assert "переведите" in body["text"].lower()
    verdict = analyze_message(body["text"], "ru")
    assert verdict["risk_level"] == "high"
    assert verdict["model_version"] == "tfidf-linearsvm-0001m"
    assert "risk_level" not in body


def test_russian_safe_text_is_not_invented(client):
    source = "Мама, я уже дома, ужин в холодильнике"
    response = _post(client, _png([source]))
    assert response.status_code == 200
    body = response.json()
    assert "дома" in body["text"].lower()
    verdict = analyze_message(body["text"], "ru")
    assert verdict["risk_level"] in {"low", "unknown"}


def test_warning_text_stays_a_warning(client):
    source = "Не сообщайте никому код из SMS"
    response = _post(client, _png([source]))
    assert response.status_code == 200
    text = response.json()["text"]
    indicators = detect_indicators(text)
    assert "fraud_warning" in indicators
    assert "otp_request" not in indicators


def test_kazakh_ocr_does_not_become_a_fraud_verdict(client):
    source = "Сәлеметсіз бе, шұғыл түрде ақшаны аударыңыз"
    response = _post(client, _png([source]))
    assert response.status_code == 200
    body = response.json()
    assert body["status"] in {"ok", "no_text"}
    assert body["engine"] == "tesseract"
    assert body["ml_language"] == "kk"
    assert body["language_locked"] is True
    assert "risk_level" not in body
    verdict = analyze_message(source, "kk")
    assert verdict["risk_level"] == "unknown"
    assert verdict["language_evaluation"] == "not_evaluated"
    if body["text"]:
        kazakh_verdict = analyze_message(body["text"], "ru")
        assert kazakh_verdict["language_evaluation"] in {"evaluated", "not_evaluated", "not_confirmed"}


def test_mixed_text_is_not_silently_treated_as_clear(client):
    source = "Срочно переведите деньги, ақшаны аударыңыз"
    response = _post(client, _png([source]))
    assert response.status_code == 200
    body = response.json()
    if "ақшаны" in body["text"] or "аударыңыз" in body["text"]:
        assert "kazakh_glyphs_detected" in body["warnings"]
        assert analyze_message(body["text"], "ru")["language_evaluation"] == "not_evaluated"


def test_blank_image_has_no_invented_text(client):
    response = _post(client, _png([]))
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "no_text"
    assert body["text"] == ""


def test_blurry_image_does_not_invent_a_clean_sentence(client):
    response = _post(client, _png(["Срочно переведите деньги"], blur=8))
    assert response.status_code == 200
    body = response.json()
    assert body["status"] in {"ok", "no_text"}
    if body["status"] == "ok":
        assert body["warnings"]


def test_unsupported_and_corrupt_files_are_rejected(client):
    gif = client.post(
        "/api/v1/analysis/screenshot",
        files={"upload": ("shot.gif", b"GIF89a" + b"\x00" * 20, "image/gif")},
    )
    assert gif.status_code == 415
    assert gif.json()["code"] == "unsupported_type"
    corrupt = _post(client, b"\x89PNG\r\n\x1a\n" + b"not-an-image")
    assert corrupt.status_code == 422
    assert corrupt.json()["code"] == "unreadable"


def test_oversized_upload_is_rejected(client):
    payload = b"\x89PNG\r\n\x1a\n" + b"0" * (8 * 1024 * 1024)
    response = _post(client, payload)
    assert response.status_code == 413
    assert response.json()["code"] == "payload_too_large"


def test_picture_without_text_is_empty(client):
    image = Image.new("RGB", (400, 240), "white")
    draw = ImageDraw.Draw(image)
    draw.ellipse((40, 40, 180, 180), outline=(0, 0, 0), width=4)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    response = _post(client, buffer.getvalue())
    assert response.status_code == 200
    assert response.json()["text"] == ""


def test_two_messages_keep_a_line_break(client):
    response = _post(client, _png(["Срочно переведите деньги на карту", "Мама, я уже дома"]))
    assert response.status_code == 200
    body = response.json()
    assert "\n" in body["text"]
    assert body["line_count"] >= 2


def test_image_metadata_is_not_returned(client):
    image = Image.new("RGB", (640, 200), "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(FONT, 36)
    draw.text((24, 70), "Обычная записка", fill=(0, 0, 0), font=font)
    meta = PngInfo()
    meta.add_text("Comment", "SECRET-LOCATION")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG", pnginfo=meta)
    response = _post(client, buffer.getvalue())
    assert response.status_code == 200
    assert "SECRET-LOCATION" not in response.text
