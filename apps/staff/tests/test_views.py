from datetime import date
from typing import cast

import pytest
from django.urls import reverse

from apps.accounts.models import Membership
from apps.staff.models import Department, TeacherProfile
from apps.tenancy.models import School
from tests.factories import MembershipFactory, SchoolFactory

pytestmark = pytest.mark.django_db


def login_membership(client, school: School, role_code: str):
    membership = cast(
        Membership,
        MembershipFactory(school=school, role_code=role_code),
    )
    client.force_login(membership.user)
    return membership


def create_teacher(school: School, employee_number: str, email: str):
    membership = cast(
        Membership,
        MembershipFactory(
            school=school,
            role_code="teacher",
            user__email=email,
        ),
    )
    return TeacherProfile.objects.create(
        school=school,
        membership=membership,
        employee_number=employee_number,
        employment_date=date(2024, 1, 8),
    )


def test_staff_index_only_lists_active_school_records(client):
    school = cast(School, SchoolFactory())
    other_school = cast(School, SchoolFactory())
    login_membership(client, school, "principal")
    create_teacher(school, "EMP-001", "teacher@first.test")
    create_teacher(other_school, "SECRET-001", "teacher@second.test")

    response = client.get(
        reverse("staff:index"),
        HTTP_HOST=f"{school.slug}.localhost",
    )

    content = response.content.decode()
    assert response.status_code == 200
    assert "data-page-header" in content
    assert "data-record-table" in content
    assert "EMP-001" in content
    assert "SECRET-001" not in content


def test_staff_index_supports_htmx_partial(client):
    school = cast(School, SchoolFactory())
    login_membership(client, school, "department_head")

    response = client.get(
        reverse("staff:index"),
        HTTP_HOST=f"{school.slug}.localhost",
        HTTP_HX_REQUEST="true",
    )

    assert response.status_code == 200
    assert 'data-staff-tables="true"' in response.content.decode()
    assert "data-empty-state" in response.content.decode()
    assert "<html" not in response.content.decode()


def test_ordinary_teacher_cannot_administer_staff(client):
    school = cast(School, SchoolFactory())
    login_membership(client, school, "teacher")

    response = client.get(
        reverse("staff:index"),
        HTTP_HOST=f"{school.slug}.localhost",
    )

    assert response.status_code == 403


def test_school_admin_can_create_department(client):
    school = cast(School, SchoolFactory())
    login_membership(client, school, "school_admin")

    response = client.post(
        reverse("staff:create", kwargs={"model_name": "department"}),
        {"code": "SCI", "name": "Sciences", "is_active": "on"},
        HTTP_HOST=f"{school.slug}.localhost",
    )

    assert response.status_code == 302
    assert Department.objects.for_school(school).get().name == "Sciences"
