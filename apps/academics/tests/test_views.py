from datetime import date
from typing import cast

import pytest
from django.urls import reverse

from apps.academics.models import AcademicYear, Grade, Stream
from apps.accounts.models import Membership
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


def test_academic_structure_only_lists_active_school_records(client):
    school = cast(School, SchoolFactory())
    other_school = cast(School, SchoolFactory())
    login_membership(client, school, "school_admin")
    Grade.objects.create(
        school=school,
        code="G7",
        name="Grade 7",
        education_level=Grade.EducationLevel.JUNIOR_SCHOOL,
        order=7,
    )
    Grade.objects.create(
        school=other_school,
        code="G8",
        name="Secret Grade",
        education_level=Grade.EducationLevel.JUNIOR_SCHOOL,
        order=8,
    )

    response = client.get(
        reverse("academics:structure"),
        HTTP_HOST=f"{school.slug}.localhost",
    )

    content = response.content.decode()
    assert response.status_code == 200
    assert "Grade 7" in content
    assert "Secret Grade" not in content


def test_academic_structure_returns_partial_for_htmx(client):
    school = cast(School, SchoolFactory())
    login_membership(client, school, "principal")

    response = client.get(
        reverse("academics:structure"),
        HTTP_HOST=f"{school.slug}.localhost",
        HTTP_HX_REQUEST="true",
    )

    assert response.status_code == 200
    assert "<html" not in response.content.decode()
    assert 'data-academic-tables="true"' in response.content.decode()


def test_teacher_cannot_configure_academic_structure(client):
    school = cast(School, SchoolFactory())
    login_membership(client, school, "teacher")

    response = client.get(
        reverse("academics:structure"),
        HTTP_HOST=f"{school.slug}.localhost",
    )

    assert response.status_code == 403


def test_stream_form_rejects_grade_from_another_school(client):
    school = cast(School, SchoolFactory())
    other_school = cast(School, SchoolFactory())
    login_membership(client, school, "school_admin")
    foreign_grade = Grade.objects.create(
        school=other_school,
        code="G7",
        name="Grade 7",
        education_level=Grade.EducationLevel.JUNIOR_SCHOOL,
        order=7,
    )

    response = client.post(
        reverse("academics:create", kwargs={"model_name": "stream"}),
        {
            "grade": str(foreign_grade.id),
            "code": "E",
            "name": "East",
            "is_active": "on",
        },
        HTTP_HOST=f"{school.slug}.localhost",
    )

    assert response.status_code == 400
    assert Stream.objects.count() == 0


def test_school_admin_can_create_academic_year(client):
    school = cast(School, SchoolFactory())
    login_membership(client, school, "school_admin")

    response = client.post(
        reverse("academics:create", kwargs={"model_name": "academic-year"}),
        {
            "name": "2026",
            "start_date": date(2026, 1, 1),
            "end_date": date(2026, 12, 31),
            "status": AcademicYear.Status.ACTIVE,
        },
        HTTP_HOST=f"{school.slug}.localhost",
    )

    assert response.status_code == 302
    assert AcademicYear.objects.for_school(school).get().name == "2026"
