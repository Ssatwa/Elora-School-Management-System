import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.accounts.models import Membership, Role
from apps.core.management.commands.seed_demo import DEMO_PASSWORD
from apps.tenancy.models import School, SchoolDomain


@pytest.mark.parametrize(
    ("role_code", "role_name", "expected_heading"),
    [
        ("school_admin", "School Admin", "School operations"),
        ("principal", "Principal", "School performance"),
        ("deputy_principal", "Deputy Principal", "Daily oversight"),
        ("teacher", "Teacher", "Teaching today"),
        ("class_teacher", "Class Teacher", "My class"),
        ("department_head", "Department Head", "Department performance"),
        ("parent", "Parent", "My learners"),
        ("learner", "Learner", "My learning"),
        ("accountant", "Accountant", "Finance overview"),
        ("librarian", "Librarian", "Library overview"),
        (
            "guidance_counsellor",
            "Guidance & Counselling Officer",
            "Learner wellbeing",
        ),
    ],
)
@pytest.mark.django_db
def test_dashboard_matches_role(client, role_code, role_name, expected_heading):
    school = School.objects.create(name="Green Hills", slug=f"green-{role_code}")
    domain = SchoolDomain.objects.create(
        school=school,
        hostname=f"{role_code.replace('_', '-')}.localhost",
        is_primary=True,
    )
    user = get_user_model().objects.create_user(f"{role_code}@example.test")
    role = Role.objects.create(code=role_code, name=role_name)
    membership = Membership.objects.create(user=user, school=school)
    membership.roles.add(role)
    client.force_login(user)

    response = client.get(
        reverse("analytics:dashboard"),
        HTTP_HOST=domain.hostname,
    )

    assert response.status_code == 200
    assert expected_heading in response.content.decode()


@pytest.mark.django_db
def test_sidebar_only_shows_modules_authorized_for_role(client):
    school = School.objects.create(name="Green Hills", slug="green-sidebar")
    domain = SchoolDomain.objects.create(
        school=school,
        hostname="green-sidebar.localhost",
        is_primary=True,
    )
    teacher = get_user_model().objects.create_user("teacher-sidebar@example.test")
    teacher_role = Role.objects.create(code="teacher", name="Teacher")
    membership = Membership.objects.create(user=teacher, school=school)
    membership.roles.add(teacher_role)
    client.force_login(teacher)

    response = client.get(reverse("analytics:dashboard"), HTTP_HOST=domain.hostname)
    content = response.content.decode()

    assert "Learners" in content
    assert "Academic structure" not in content
    assert ">Staff<" not in content
    assert 'href="/dashboard/"' in content
    assert 'aria-current="page"' in content
    assert 'href="/attendance/"' in content
    assert 'href="/finance/"' not in content


@pytest.mark.django_db
def test_seeded_school_dashboard_shows_live_metrics_and_chart(client, settings):
    from django.core.management import call_command

    settings.ALLOW_DEMO_SEED = True
    call_command("seed_demo")
    user = get_user_model().objects.get(email="school_admin@green-hills.localhost")
    assert user.check_password(DEMO_PASSWORD)
    client.force_login(user)

    response = client.get(
        reverse("analytics:dashboard"),
        HTTP_HOST="green-hills.localhost",
    )

    content = response.content.decode()
    assert response.status_code == 200
    assert "Total learners" in content
    assert "Fee collection" in content
    assert "dashboardChart" in content
    assert "Your workspace is ready" not in content
