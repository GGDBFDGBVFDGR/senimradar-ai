import logging


SECRET = "OTP-CODE-998877-DO-NOT-LOG"


def test_text_analysis_is_unavailable_and_not_a_prediction(client):
    response = client.post(
        "/api/v1/analysis/text",
        json={"text": "Проверьте это сообщение", "language": "ru"},
    )
    assert response.status_code == 503
    assert response.json() == {
        "status": "unavailable",
        "code": "model_not_configured",
        "stage": 2,
        "input_type": "text",
        "language": "ru",
        "message": "Text fraud analysis model is not configured.",
        "model_version": None,
        "risk_level": None,
        "risk_score": None,
    }
    assert "explanation" not in response.json()
    assert "detected_threats" not in response.json()


def test_submitted_text_is_not_logged_or_echoed(client, caplog):
    with caplog.at_level(logging.DEBUG):
        response = client.post(
            "/api/v1/analysis/text",
            json={"text": SECRET, "language": "ru"},
        )
    assert response.status_code == 503
    assert SECRET not in response.text
    assert SECRET not in caplog.text


def test_validation_error_does_not_echo_submission(client):
    response = client.post(
        "/api/v1/analysis/text",
        json={"text": SECRET, "language": "de"},
    )
    assert response.status_code == 422
    body = response.json()
    assert body["status"] == "error"
    assert body["code"] == "validation_error"
    assert SECRET not in response.text
    assert "input" not in response.text


def test_blank_text_is_rejected(client):
    response = client.post(
        "/api/v1/analysis/text",
        json={"text": "   ", "language": "kk"},
    )
    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"


def test_oversized_payload_is_rejected(client):
    response = client.post(
        "/api/v1/analysis/text",
        content="{" + ("x" * 60000),
        headers={"content-type": "application/json"},
    )
    assert response.status_code == 413
    assert response.json()["code"] == "payload_too_large"
