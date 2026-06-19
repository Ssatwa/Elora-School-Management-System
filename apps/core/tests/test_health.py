from apps.tenancy.models import School, SchoolDomain


def test_root_redirects_to_dashboard(client, db):
    school = School.objects.create(name="Green Hills", slug="green-hills")
    SchoolDomain.objects.create(
        school=school,
        hostname="green-hills.localhost",
        is_primary=True,
    )

    response = client.get("/", HTTP_HOST="green-hills.localhost")

    assert response.status_code == 302
    assert response.url == "/dashboard/"


def test_health_response_has_request_id(client):
    response = client.get("/health/")
    assert response.status_code == 200
    assert response.headers["X-Request-ID"]


def test_readiness_reports_database(client, db):
    response = client.get("/ready/")
    assert response.json() == {
        "status": "ready",
        "database": "ok",
        "service": "elora",
    }
