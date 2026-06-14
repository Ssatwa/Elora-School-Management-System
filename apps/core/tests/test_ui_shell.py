from pathlib import Path

import pytest
from django.contrib.auth import get_user_model
from django.template import engines
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
    assert content.index("/static/js/app.js") < content.index("alpinejs")
    assert 'id="primary-navigation"' in content
    assert 'aria-label="Primary navigation"' in content
    assert 'aria-current="page"' in content
    assert "data-mobile-sidebar" in content
    assert "data-sidebar-collapse" in content
    assert "data-mobile-sidebar-backdrop" in content
    assert 'aria-label="Search Elora"' in content
    assert 'aria-label="Notifications"' in content
    assert 'aria-label="User menu"' in content
    assert "Overview" in content
    assert "People" in content
    assert "Learning" in content
    assert "Operations" in content


def test_shell_javascript_registers_alpine_state_with_safe_storage():
    content = Path("static/js/app.js").read_text()

    assert 'Alpine.data("eloraShell"' in content
    assert "safeStorage.get(" in content
    assert "safeStorage.set(" in content


def test_theme_bootstrap_guards_storage_access():
    content = Path("templates/layouts/app.html").read_text()

    assert "function readStoredTheme()" in content
    assert "try {" in content
    assert "catch" in content


@pytest.mark.parametrize(
    ("template_name", "context", "marker", "expected_text"),
    [
        (
            "components/page_header.html",
            {
                "eyebrow": "People",
                "title": "Learners",
                "description": "Manage learner records.",
            },
            "data-page-header",
            "Learners",
        ),
        (
            "components/metric_card.html",
            {"label": "Attendance rate", "value": "94%", "tone": "success"},
            "data-metric-card",
            "94%",
        ),
        (
            "components/empty_state.html",
            {"title": "No records", "description": "Add the first record."},
            "data-empty-state",
            "No records",
        ),
        (
            "components/table_shell.html",
            {"title": "Recent records", "description": "Latest updates."},
            "data-table-shell",
            "Recent records",
        ),
    ],
)
def test_shared_component_contracts(template_name, context, marker, expected_text):
    template = engines["django"].from_string(
        f'{{% include "{template_name}" %}}'
    )

    content = template.render(context)

    assert marker in content
    assert expected_text in content
    assert "<h1" in content if template_name.endswith("page_header.html") else True


def test_message_component_exposes_accessible_status_roles():
    content = Path("templates/components/messages.html").read_text()

    assert 'role="alert"' in content
    assert 'role="status"' in content
