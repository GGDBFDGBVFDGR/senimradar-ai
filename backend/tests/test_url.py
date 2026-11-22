import socket
from pathlib import Path
from urllib import request

from app.ml.registry import ARTIFACT_DIR as TEXT_ARTIFACTS
from app.url.registry import reset_url_runtime


def test_text_model_pointer_is_unchanged():
    pointer = (TEXT_ARTIFACTS / "active_model.json").read_text(encoding="utf-8")
    assert "tfidf-linearsvm-0001m" in pointer
    assert "url-tfidf" not in pointer


def test_url_is_not_fetched(client, monkeypatch):
    def fail(*_args, **_kwargs):
        raise AssertionError("network")

    monkeypatch.setattr(socket, "getaddrinfo", fail)
    monkeypatch.setattr(socket, "create_connection", fail)
    monkeypatch.setattr(request, "urlopen", fail)
    response = client.post("/api/v1/analysis/url", json={"url": "https://example.com/about"})
    assert response.status_code in {200, 503}
    assert "example.com" not in response.text


def test_internal_and_unsupported_addresses_are_not_scored(client):
    internal = client.post("/api/v1/analysis/url", json={"url": "http://127.0.0.1/admin"})
    assert internal.status_code == 200
    assert internal.json()["status"] == "limited"
    assert internal.json()["classified"] is False
    assert internal.json()["risk_level"] == "unknown"
    assert internal.json()["risk_score"] is None

    private = client.post("/api/v1/analysis/url", json={"url": "http://192.168.0.8/"})
    assert private.json()["code"] == "internal_address"
    assert private.json()["classified"] is False

    scheme = client.post("/api/v1/analysis/url", json={"url": "ftp://example.com/file"})
    assert scheme.json()["code"] == "unsupported_scheme"
    assert scheme.json()["classified"] is False

    missing = client.post("/api/v1/analysis/url", json={"url": "example.com/login"})
    assert missing.json()["code"] == "scheme_required"

    script = client.post("/api/v1/analysis/url", json={"url": "javascript:alert(1)"})
    assert script.json()["code"] == "unsupported_scheme"


def test_damaged_ocr_url_is_not_classified(client):
    response = client.post("/api/v1/analysis/url", json={"url": "һЧрв://ехатріе.сот/рау"})
    body = response.json()
    assert response.status_code == 200
    assert body["status"] == "needs_review"
    assert body["code"] == "ocr_damaged"
    assert body["classified"] is False
    assert body["risk_level"] == "unknown"
    assert body["model_version"] is None
    assert "ехатріе" not in response.text


def test_punycode_is_scored_only_when_the_model_exists(client):
    response = client.post("/api/v1/analysis/url", json={"url": "https://xn--80ak6aa92e.com/login"})
    body = response.json()
    if response.status_code == 503:
        assert body["risk_level"] is None
        assert body["code"] == "model_not_configured"
        return
    assert body["classified"] is True
    assert body["risk_score"] is None
    assert "punycode" in body["indicators"]
    assert body["model_version"]
    assert "xn--80ak6aa92e.com" not in response.text


def test_missing_url_model_does_not_invent_a_score(client, monkeypatch):
    monkeypatch.setattr("app.url.registry.pointer_path", lambda: Path("/tmp/senimradar-missing-url-model.json"))
    reset_url_runtime()
    try:
        response = client.post("/api/v1/analysis/url", json={"url": "https://example.com/"})
        assert response.status_code == 503
        body = response.json()
        assert body["status"] == "unavailable"
        assert body["risk_level"] is None
        assert body["risk_score"] is None
    finally:
        reset_url_runtime()


def test_query_string_stays_unopened(client):
    response = client.post(
        "/api/v1/analysis/url",
        json={"url": "https://example.com/search?q=weather&page=2"},
    )
    assert response.status_code in {200, 503}
    assert "weather" not in response.text
