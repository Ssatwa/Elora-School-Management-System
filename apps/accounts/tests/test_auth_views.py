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
def test_login_page_uses_branded_public_shell(client):
    response = client.get(
        reverse("accounts:login"),
        HTTP_HOST="localhost:56274",
    )
    content = response.content.decode()

    assert response.status_code == 200
    assert "data-public-shell" in content
    assert "Powering Modern Education" in content
    assert 'autocomplete="current-password"' in content
    assert 'autocomplete="username"' in content


@pytest.mark.django_db
def test_school_domain_login_redirects_to_universal_login(client):
    _, domain = create_school_domain("green-hills")

    response = client.get(
        reverse("accounts:login"),
        HTTP_HOST=domain.hostname,
    )

    assert response.status_code == 302
    assert response.url == "http://localhost/accounts/login/"


@pytest.mark.django_db
def test_platform_login_does_not_redirect_to_itself_when_school_session_exists(client):
    school, _ = create_school_domain("green-hills")
    session = client.session
    session["active_school_id"] = str(school.id)
    session.save()

    response = client.get(
        reverse("accounts:login"),
        HTTP_HOST="localhost:56274",
    )

    assert response.status_code == 200
    assert "data-public-shell" in response.content.decode()


@pytest.mark.django_db
def test_member_can_log_into_universal_login(client):
    school, _ = create_school_domain("green-hills")
    user = get_user_model().objects.create_user(
        "admin@green-hills.test",
        password="correct-horse",
    )
    Membership.objects.create(school=school, user=user)

    response = client.post(
        reverse("accounts:login"),
        {"username": user.email, "password": "correct-horse"},
        HTTP_HOST="localhost:56274",
    )

    assert response.status_code == 302
    assert response.url == "/dashboard/"
    assert str(client.session["active_school_id"]) == str(school.id)


@pytest.mark.django_db
def test_user_without_school_membership_cannot_log_into_universal_login(client):
    user = get_user_model().objects.create_user(
        "outsider@example.test",
        password="correct-horse",
    )

    response = client.post(
        reverse("accounts:login"),
        {"username": user.email, "password": "correct-horse"},
        HTTP_HOST="localhost:56274",
    )

    assert response.status_code == 200
    assert "Your account is not linked to an active school." in response.content.decode()


@pytest.mark.django_db
def test_logout_from_school_dashboard_redirects_to_universal_login(client):
    school, domain = create_school_domain("green-hills")
    user = get_user_model().objects.create_user(
        "admin@green-hills.test",
        password="correct-horse",
    )
    Membership.objects.create(school=school, user=user)
    client.force_login(user)

    response = client.post(
        reverse("accounts:logout"),
        HTTP_HOST=f"{domain.hostname}:56274",
    )

    assert response.status_code == 302
    assert response.url == "http://localhost:56274/accounts/login/"

    dashboard = client.get("/dashboard/", HTTP_HOST=f"{domain.hostname}:56274")
    assert dashboard.status_code == 302
    assert "/accounts/login/" in dashboard.url


@pytest.mark.django_db
def test_platform_login_redirects_single_school_user_to_school_dashboard(client):
    school, _ = create_school_domain("green-hills")
    user = get_user_model().objects.create_user(
        "admin@example.test",
        password="correct-horse",
    )
    Membership.objects.create(school=school, user=user)

    response = client.post(
        reverse("accounts:login"),
        {"username": user.email, "password": "correct-horse"},
        HTTP_HOST="localhost:56274",
    )

    assert response.status_code == 302
    assert response.url == "/dashboard/"
    assert str(client.session["active_school_id"]) == str(school.id)


@pytest.mark.django_db
def test_platform_login_sends_multi_school_user_to_school_chooser(client):
    first, _ = create_school_domain("green-hills")
    second, _ = create_school_domain("sunrise")
    user = get_user_model().objects.create_user(
        "leader@example.test",
        password="correct-horse",
    )
    Membership.objects.create(school=first, user=user)
    Membership.objects.create(school=second, user=user)

    response = client.post(
        reverse("accounts:login"),
        {"username": user.email, "password": "correct-horse"},
        HTTP_HOST="localhost:56274",
    )

    assert response.status_code == 302
    assert response.url == reverse("accounts:select_school")

    chooser = client.get(response.url, HTTP_HOST="localhost:56274")
    content = chooser.content.decode()

    assert chooser.status_code == 200
    assert "Choose your school" in content
    assert "Green Hills" in content
    assert "Sunrise" in content


@pytest.mark.django_db
def test_school_chooser_redirects_to_linked_school_dashboard(client):
    school, _ = create_school_domain("green-hills")
    user = get_user_model().objects.create_user(
        "teacher@example.test",
        password="correct-horse",
    )
    Membership.objects.create(school=school, user=user)
    client.force_login(user)

    response = client.post(
        reverse("accounts:select_school"),
        {"school": str(school.id)},
        HTTP_HOST="localhost:56274",
    )

    assert response.status_code == 302
    assert response.url == "/dashboard/"
    assert str(client.session["active_school_id"]) == str(school.id)


@pytest.mark.django_db
def test_school_chooser_rejects_unlinked_school(client):
    user_school, _ = create_school_domain("green-hills")
    other_school, _ = create_school_domain("sunrise")
    user = get_user_model().objects.create_user(
        "teacher@example.test",
        password="correct-horse",
    )
    Membership.objects.create(school=user_school, user=user)
    client.force_login(user)

    response = client.post(
        reverse("accounts:select_school"),
        {"school": str(other_school.id)},
        HTTP_HOST="localhost:56274",
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_platform_dashboard_redirects_authenticated_user_to_school_chooser(client):
    school, _ = create_school_domain("green-hills")
    user = get_user_model().objects.create_user(
        "teacher@example.test",
        password="correct-horse",
    )
    Membership.objects.create(school=school, user=user)
    client.force_login(user)

    response = client.get("/dashboard/", HTTP_HOST="localhost:56274")

    assert response.status_code == 302
    assert response.url == reverse("accounts:select_school")


@pytest.mark.django_db
def test_platform_dashboard_uses_active_school_from_session(client):
    school, _ = create_school_domain("green-hills")
    user = get_user_model().objects.create_user(
        "teacher@example.test",
        password="correct-horse",
    )
    Membership.objects.create(school=school, user=user)
    client.force_login(user)
    session = client.session
    session["active_school_id"] = str(school.id)
    session.save()

    response = client.get("/dashboard/", HTTP_HOST="localhost:56274")

    assert response.status_code == 200
    assert response.headers["X-Elora-School"] == str(school.id)
