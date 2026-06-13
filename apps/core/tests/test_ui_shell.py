import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.accounts.models import Membership, Role
from apps.tenancy.models import School, SchoolDomain


@pytest.mark.django_db
def test_authenticated_pages_render_premium_shell(client):
    school = School.objects.create(name="Green Hills", slug="green-shell")
    domain = SchoolDomain.objects.create(
        school=school,
        hostname="green-shell.localhost",
        is_primary=True,
    )
    user = get_user_model().objects.create_user("school-admin-shell@example.test")
    role = Role.objects.create(code="school_admin", name="School Admin")
    membership = Membership.objects.create(user=user, school=school)
    membership.roles.add(role)
    client.force_login(user)

    response = client.get(
        reverse("analytics:dashboard"),
        HTTP_HOST=domain.hostname,
    )
    content = response.content.decode()

    assert response.status_code == 200
    assert "data-elora-shell" in content
    assert 'href="#main-content"' in content
    assert 'x-data="eloraShell"' in content
    assert "data-theme-toggle" in content
    assert 'aria-controls="primary-navigation"' in content
    assert 'id="main-content"' in content
