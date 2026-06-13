import pytest

from apps.tenancy.models import School, SchoolDomain


@pytest.mark.django_db
def test_known_subdomain_sets_request_school(client):
    school = School.objects.create(name="Green Hills", slug="green-hills")
    SchoolDomain.objects.create(
        school=school,
        hostname="green-hills.localhost",
        is_primary=True,
    )

    response = client.get("/health/", HTTP_HOST="green-hills.localhost")

    assert response.status_code == 200
    assert response.headers["X-Elora-School"] == str(school.id)


@pytest.mark.django_db
def test_unknown_subdomain_returns_404(client):
    response = client.get("/health/", HTTP_HOST="unknown.localhost")

    assert response.status_code == 404
