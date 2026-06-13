from datetime import date
from typing import cast

import pytest
from django.urls import reverse

from apps.academics.models import AcademicYear, Grade, Stream
from apps.accounts.models import Membership
from apps.learners.models import Enrollment, Learner, TransferRecord
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


def create_academic_context(school: School):
    year = AcademicYear.objects.create(
        school=school,
        name="2026",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
        status=AcademicYear.Status.ACTIVE,
    )
    grade = Grade.objects.create(
        school=school,
        code="G7",
        name="Grade 7",
        education_level=Grade.EducationLevel.JUNIOR_SCHOOL,
        order=7,
    )
    stream = Stream.objects.create(
        school=school,
        grade=grade,
        code="E",
        name="East",
    )
    return year, grade, stream


def create_learner(school: School, admission_number: str):
    return Learner.objects.create(
        school=school,
        admission_number=admission_number,
        first_name="Amina",
        last_name="Kamau",
        date_of_birth=date(2013, 6, 12),
        gender=Learner.Gender.FEMALE,
        admission_date=date(2026, 1, 6),
    )


def test_learner_index_only_lists_active_school_records(client):
    school = cast(School, SchoolFactory())
    other_school = cast(School, SchoolFactory())
    login_membership(client, school, "teacher")
    create_learner(school, "2026-0001")
    create_learner(other_school, "SECRET-0001")

    response = client.get(
        reverse("learners:index"),
        HTTP_HOST=f"{school.slug}.localhost",
    )

    content = response.content.decode()
    assert response.status_code == 200
    assert "2026-0001" in content
    assert "SECRET-0001" not in content


def test_learner_index_supports_htmx_partial(client):
    school = cast(School, SchoolFactory())
    login_membership(client, school, "class_teacher")

    response = client.get(
        reverse("learners:index"),
        HTTP_HOST=f"{school.slug}.localhost",
        HTTP_HX_REQUEST="true",
    )

    assert response.status_code == 200
    assert 'data-learner-table="true"' in response.content.decode()
    assert "<html" not in response.content.decode()


def test_school_admin_can_complete_admission_from_form(client):
    school = cast(School, SchoolFactory())
    login_membership(client, school, "school_admin")
    year, grade, stream = create_academic_context(school)

    response = client.post(
        reverse("learners:admit"),
        {
            "first_name": "Amina",
            "last_name": "Kamau",
            "date_of_birth": "2013-06-12",
            "gender": Learner.Gender.FEMALE,
            "academic_year": str(year.id),
            "grade": str(grade.id),
            "stream": str(stream.id),
            "admission_date": "2026-01-06",
            "guardian_first_name": "Wanjiku",
            "guardian_last_name": "Kamau",
            "guardian_email": "parent@example.test",
            "guardian_phone_number": "+254700000001",
            "guardian_relationship": "mother",
            "blood_group": "O+",
            "allergies": "Peanuts",
        },
        HTTP_HOST=f"{school.slug}.localhost",
    )

    learner = Learner.objects.for_school(school).get()
    assert response.status_code == 302
    assert response.url == reverse("learners:detail", kwargs={"learner_id": learner.id})
    assert learner.enrollments.get().stream == stream


def test_cross_school_learner_detail_is_not_found(client):
    school = cast(School, SchoolFactory())
    other_school = cast(School, SchoolFactory())
    login_membership(client, school, "principal")
    learner = create_learner(other_school, "2026-0001")

    response = client.get(
        reverse("learners:detail", kwargs={"learner_id": learner.id}),
        HTTP_HOST=f"{school.slug}.localhost",
    )

    assert response.status_code == 404


def test_school_admin_can_transfer_learner_from_detail(client):
    school = cast(School, SchoolFactory())
    login_membership(client, school, "school_admin")
    year, grade, stream = create_academic_context(school)
    learner = create_learner(school, "2026-0001")
    Enrollment.objects.create(
        school=school,
        learner=learner,
        academic_year=year,
        grade=grade,
        stream=stream,
        start_date=date(2026, 1, 6),
    )

    response = client.post(
        reverse("learners:transfer", kwargs={"learner_id": learner.id}),
        {
            "destination_school_name": "Lakeview Academy",
            "transfer_date": "2026-06-30",
            "reason": "Family relocation",
            "export_reference": "EXP-2026-0001",
        },
        HTTP_HOST=f"{school.slug}.localhost",
    )

    assert response.status_code == 302
    assert TransferRecord.objects.get(learner=learner).status == (
        TransferRecord.Status.COMPLETED
    )
