from app.ml.inference import analyze_message
from app.ocr.score import character_error_rate, word_error_rate
from tests.ocr_samples import measure


def test_error_rates_count_words_and_characters():
    assert character_error_rate("әлемет", "элемет") == 1 / 6
    assert word_error_rate("ақшаны аударыңыз", "акшаны аударыныз") == 1


def test_russian_choice_keeps_apple_vision(client):
    from tests.ocr_samples import SAMPLES, render_sample

    sample = SAMPLES[0]
    response = client.post(
        "/api/v1/analysis/screenshot",
        files={"upload": ("shot.png", render_sample(sample), "image/png")},
        data={"language": "ru"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["engine"] == "apple_vision"
    assert body["ml_language"] == "ru"
    assert body["language_locked"] is False
    assert character_error_rate(sample["text"], body["text"]) == 0


def test_auto_does_not_call_damaged_text_russian(client):
    from app.ocr.tesseract_ocr import kazakh_ocr_ready
    from tests.ocr_samples import SAMPLES, render_sample

    sample = SAMPLES[1]
    response = client.post(
        "/api/v1/analysis/screenshot",
        files={"upload": ("shot.png", render_sample(sample), "image/png")},
        data={"language": "auto"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "risk_level" not in body
    if kazakh_ocr_ready():
        assert body["engine"] == "tesseract"
        assert body["text"] == sample["text"]
        assert body["ml_language"] == "kk"
        assert body["language_locked"] is True
    else:
        assert body["ml_language"] == "unconfirmed"
        assert body["language_locked"] is False
        assert "language_unconfirmed" in body["warnings"]


def test_kazakh_choice_does_not_fall_back_to_russian_ocr(client):
    from app.ocr.tesseract_ocr import kazakh_ocr_ready
    from tests.ocr_samples import SAMPLES, render_sample

    sample = SAMPLES[1]
    response = client.post(
        "/api/v1/analysis/screenshot",
        files={"upload": ("shot.png", render_sample(sample), "image/png")},
        data={"language": "kk"},
    )
    body = response.json()
    assert "risk_level" not in body
    if kazakh_ocr_ready():
        assert response.status_code == 200
        assert body["engine"] == "tesseract"
        assert body["text"] == sample["text"]
        assert body["ml_language"] == "kk"
        assert body["language_locked"] is True
    else:
        assert response.status_code == 503
        assert body["code"] == "kazakh_ocr_unavailable"


def test_kazakh_image_choice_blocks_russian_model_on_the_server(client):
    message = "Служба банка: срочно переведите деньги на карту"
    response = client.post(
        "/api/v1/analysis/text",
        json={"text": message, "language": "ru", "image_language": "kk"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["language"] == "kk"
    assert body["risk_level"] == "unknown"
    assert body["language_evaluation"] == "not_evaluated"
    direct = analyze_message(message, "ru")
    assert direct["risk_level"] == "high"


def test_vision_misses_kazakh_letters_on_synthetic_pages():
    rows = {row["name"]: row for row in measure("vision")}
    assert rows["ru_clean"]["cer"] == 0
    assert rows["ru_clean"]["wer"] == 0
    assert rows["kk_letters"]["cer"] > 0
    assert len(rows["kk_letters"]["kazakh_letters_kept"]) < 18
    assert rows["kk_clean"]["status"] == "ok"
