import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.accounts.models import Membership
from apps.tenancy.models import School, SchoolDomain


def create_school_domain(slug):
    school = School.objects.create(name=slug.replace("-", " ").title(), slug=slug)
    domain = SchoolDomain.objects.create(
        school=school,
        hostname=f"{slug}.localhost",
        is_primary=True,
    )
    return school, domain


@pytest.mark.django_db
def test_member_can_log_into_school(client):
    school, domain = create_school_domain("green-hills")
    user = get_user_model().objects.create_user(
        "admin@green-hills.test",
        password="correct-horse",
    )
    Membership.objects.create(school=school, user=user)

    response = client.post(
        reverse("accounts:login"),
        {"username": user.email, "password": "correct-horse"},
        HTTP_HOST=domain.hostname,
    )

    assert response.status_code == 302
    assert response.url == "/dashboard/"


@pytest.mark.django_db
def test_non_member_cannot_log_into_school(client):
    _, domain = create_school_domain("green-hills")
    user = get_user_model().objects.create_user(
        "outsider@example.test",
        password="correct-horse",
    )

    response = client.post(
        reverse("accounts:login"),
        {"username": user.email, "password": "correct-horse"},
        HTTP_HOST=domain.hostname,
    )

    assert response.status_code == 200
    assert "You do not have access to this school." in response.content.decode()
