from django.conf import settings
from django.urls import reverse


def test_project_uses_nairobi_timezone():
    assert settings.TIME_ZONE == "Africa/Nairobi"


def test_health_url_is_registered(client):
    response = client.get(reverse("health"))
    assert response.status_code == 200
