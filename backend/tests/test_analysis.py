import logging


SECRET = "OTP-CODE-998877-DO-NOT-LOG"


def test_text_analysis_returns_a_model_result_without_a_percent(client):
    message = "Служба безопасности банка: карта заблокирована, срочно сообщите код и переведите деньги"
    response = client.post(
        "/api/v1/analysis/text",
        json={"text": message, "language": "ru"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["risk_level"] in {"low", "medium", "high", "unknown"}
    assert body["risk_score"] is None
    from app.ml.registry import load_runtime

    runtime = load_runtime()
    assert runtime is not None
    assert body["model_version"] == runtime["payload"]["model_version"]
    assert body["language_evaluation"] == "evaluated"
    assert message not in response.text
    assert "not_a_proof" in body["limitations"]


def test_missing_model_stays_unavailable(client, monkeypatch):
    monkeypatch.setenv("SENIMRADAR_MODEL_PATH", "/tmp/senimradar-missing-model.joblib")
    from app.ml.registry import reset_runtime

    reset_runtime()
    response = client.post(
        "/api/v1/analysis/text",
        json={"text": "Проверьте это сообщение", "language": "ru"},
    )
    assert response.status_code == 503
    assert response.json()["code"] == "model_not_configured"
    assert response.json()["risk_level"] is None
    reset_runtime()


def test_submitted_text_is_not_logged_or_echoed(client, caplog):
    with caplog.at_level(logging.DEBUG):
        response = client.post(
            "/api/v1/analysis/text",
            json={"text": SECRET, "language": "ru"},
        )
    assert response.status_code == 200
    assert SECRET not in response.text
    assert "998877" not in response.text
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
