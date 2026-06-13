def test_health_response_has_request_id(client):
    response = client.get("/health/")
    assert response.status_code == 200
    assert response.headers["X-Request-ID"]


def test_readiness_reports_database(client, db):
    response = client.get("/ready/")
    assert response.json() == {"status": "ready", "database": "ok"}
