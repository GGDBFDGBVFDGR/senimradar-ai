def test_health_is_live(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "SenimRadar AI"
    assert body["version"] == "0.1.0"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["cache-control"] == "no-store"


def test_ready_reports_database_without_crashing(client):
    response = client.get("/api/v1/health/ready")
    assert response.status_code in {200, 503}
    body = response.json()
    if response.status_code == 200:
        assert body == {"status": "ok", "database": "ok"}
    else:
        assert body == {"status": "degraded", "database": "unavailable"}


def test_capabilities_do_not_claim_a_model(client):
    response = client.get("/api/v1/system/capabilities")
    assert response.status_code == 200
    body = response.json()
    assert body["stage"] == 1
    assert body["model_configured"] is False
    assert body["third_party_ai_enabled"] is False
    text_analysis = next(item for item in body["capabilities"] if item["key"] == "text_analysis")
    assert text_analysis["status"] == "unavailable"
    assert text_analysis["note_code"] == "model_not_configured"


def test_unknown_route_is_not_a_server_error(client):
    response = client.get("/api/v1/missing")
    assert response.status_code == 404


def test_cors_allows_local_frontend_only(client):
    allowed = client.get("/api/v1/health", headers={"Origin": "http://127.0.0.1:5173"})
    assert allowed.headers["access-control-allow-origin"] == "http://127.0.0.1:5173"

    blocked = client.get("/api/v1/health", headers={"Origin": "http://evil.example"})
    assert "access-control-allow-origin" not in blocked.headers
