from datetime import date
from typing import cast

import pytest
from django.urls import reverse

from apps.academics.models import AcademicYear, Grade, Stream, StreamLabel
from apps.accounts.models import Membership
from apps.attendance.models import AttendanceRegister
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
    assert "data-page-header" in content
    assert "data-record-table" in content
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
    assert "data-empty-state" in response.content.decode()


def test_teacher_cannot_configure_academic_structure(client):
    school = cast(School, SchoolFactory())
    login_membership(client, school, "teacher")

    response = client.get(
        reverse("academics:structure"),
        HTTP_HOST=f"{school.slug}.localhost",
    )

    assert response.status_code == 403


def test_stream_form_does_not_ask_for_grade(client):
    school = cast(School, SchoolFactory())
    login_membership(client, school, "school_admin")

    response = client.get(
        reverse("academics:structure"),
        HTTP_HOST=f"{school.slug}.localhost",
    )

    stream_form = response.context["stream_form"]
    content = response.content.decode()
    assert response.status_code == 200
    assert "grade" not in stream_form.fields
    assert 'name="grade"' not in content


def test_school_level_stream_creation_connects_to_existing_grades(client):
    school = cast(School, SchoolFactory())
    other_school = cast(School, SchoolFactory())
    login_membership(client, school, "school_admin")
    grade_one = Grade.objects.create(
        school=school,
        code="G1",
        name="Grade 1",
        education_level=Grade.EducationLevel.PRIMARY,
        order=1,
    )
    grade_two = Grade.objects.create(
        school=school,
        code="G2",
        name="Grade 2",
        education_level=Grade.EducationLevel.PRIMARY,
        order=2,
    )
    inactive_grade = Grade.objects.create(
        school=school,
        code="G9",
        name="Grade 9",
        education_level=Grade.EducationLevel.JUNIOR_SCHOOL,
        order=9,
        is_active=False,
    )
    other_grade = Grade.objects.create(
        school=other_school,
        code="G7",
        name="Grade 7",
        education_level=Grade.EducationLevel.JUNIOR_SCHOOL,
        order=7,
    )

    response = client.post(
        reverse("academics:create", kwargs={"model_name": "stream"}),
        {
            "code": "E",
            "name": "East",
            "is_active": "on",
        },
        HTTP_HOST=f"{school.slug}.localhost",
        follow=True,
    )

    content = response.content.decode()
    assert response.status_code == 200
    assert Stream.objects.for_school(school).filter(grade=grade_one, name="East").exists()
    assert Stream.objects.for_school(school).filter(grade=grade_two, name="East").exists()
    assert not Stream.objects.for_school(school).filter(grade=inactive_grade, name="East").exists()
    assert not Stream.objects.for_school(other_school).filter(grade=other_grade, name="East").exists()
    assert "Grade 1 East" in content
    assert "Grade 2 East" in content


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


def test_creating_grade_copies_existing_school_stream_labels(client):
    school = cast(School, SchoolFactory())
    other_school = cast(School, SchoolFactory())
    login_membership(client, school, "school_admin")
    grade_one = Grade.objects.create(
        school=school,
        code="G1",
        name="Grade 1",
        education_level=Grade.EducationLevel.PRIMARY,
        order=1,
    )
    Grade.objects.create(
        school=other_school,
        code="G1",
        name="Grade 1",
        education_level=Grade.EducationLevel.PRIMARY,
        order=1,
    )
    StreamLabel.objects.create(school=school, code="E", name="East")
    StreamLabel.objects.create(school=school, code="W", name="West")
    StreamLabel.objects.create(
        school=other_school,
        code="N",
        name="North",
    )

    response = client.post(
        reverse("academics:create", kwargs={"model_name": "grade"}),
        {
            "code": "G7",
            "name": "Grade 7",
            "education_level": Grade.EducationLevel.JUNIOR_SCHOOL,
            "order": 7,
            "is_active": "on",
        },
        HTTP_HOST=f"{school.slug}.localhost",
        follow=True,
    )

    grade_seven = Grade.objects.for_school(school).get(code="G7")
    stream_names = list(
        Stream.objects.for_school(school)
        .filter(grade=grade_seven)
        .order_by("name")
        .values_list("name", flat=True)
    )
    content = response.content.decode()
    assert response.status_code == 200
    assert stream_names == ["East", "West"]
    assert not Stream.objects.for_school(school).filter(grade=grade_seven, name="North").exists()
    assert "Grade 7" in content
    assert "East" in content
    assert "West" in content


def test_creating_grade_without_existing_streams_only_creates_grade(client):
    school = cast(School, SchoolFactory())
    login_membership(client, school, "school_admin")

    response = client.post(
        reverse("academics:create", kwargs={"model_name": "grade"}),
        {
            "code": "G2",
            "name": "Grade 2",
            "education_level": Grade.EducationLevel.PRIMARY,
            "order": 2,
            "is_active": "on",
        },
        HTTP_HOST=f"{school.slug}.localhost",
    )

    grade = Grade.objects.for_school(school).get(code="G2")
    assert response.status_code == 302
    assert not Stream.objects.for_school(school).filter(grade=grade).exists()


def test_manual_stream_creation_appears_in_academic_structure(client):
    school = cast(School, SchoolFactory())
    login_membership(client, school, "school_admin")
    grade = Grade.objects.create(
        school=school,
        code="G7",
        name="Grade 7",
        education_level=Grade.EducationLevel.JUNIOR_SCHOOL,
        order=7,
    )

    response = client.post(
        reverse("academics:create", kwargs={"model_name": "stream"}),
        {
            "code": "E",
            "name": "East",
            "is_active": "on",
        },
        HTTP_HOST=f"{school.slug}.localhost",
        follow=True,
    )

    content = response.content.decode()
    assert response.status_code == 200
    assert Stream.objects.for_school(school).filter(grade=grade, name="East").exists()
    assert "Grade 7" in content
    assert "East" in content


def test_school_admin_can_delete_school_level_stream_label(client):
    school = cast(School, SchoolFactory())
    other_school = cast(School, SchoolFactory())
    login_membership(client, school, "school_admin")
    grade = Grade.objects.create(
        school=school,
        code="G7",
        name="Grade 7",
        education_level=Grade.EducationLevel.JUNIOR_SCHOOL,
        order=7,
    )
    other_grade = Grade.objects.create(
        school=other_school,
        code="G7",
        name="Grade 7",
        education_level=Grade.EducationLevel.JUNIOR_SCHOOL,
        order=7,
    )
    label = StreamLabel.objects.create(school=school, code="E", name="East")
    other_label = StreamLabel.objects.create(school=other_school, code="E", name="East")
    Stream.objects.create(school=school, grade=grade, code="E", name="East")
    Stream.objects.create(school=other_school, grade=other_grade, code="E", name="East")

    response = client.post(
        reverse("academics:delete_stream_label", kwargs={"label_id": label.id}),
        HTTP_HOST=f"{school.slug}.localhost",
        follow=True,
    )

    content = response.content.decode()
    assert response.status_code == 200
    assert not StreamLabel.objects.for_school(school).filter(id=label.id).exists()
    assert not Stream.objects.for_school(school).filter(name="East").exists()
    assert StreamLabel.objects.for_school(other_school).filter(id=other_label.id).exists()
    assert Stream.objects.for_school(other_school).filter(name="East").exists()
    assert "East stream deleted." in content


def test_teacher_cannot_delete_stream_label(client):
    school = cast(School, SchoolFactory())
    login_membership(client, school, "teacher")
    label = StreamLabel.objects.create(school=school, code="E", name="East")

    response = client.post(
        reverse("academics:delete_stream_label", kwargs={"label_id": label.id}),
        HTTP_HOST=f"{school.slug}.localhost",
    )

    assert response.status_code == 403
    assert StreamLabel.objects.for_school(school).filter(id=label.id).exists()


def test_delete_stream_label_deactivates_protected_streams(client):
    school = cast(School, SchoolFactory())
    login_membership(client, school, "school_admin")
    grade = Grade.objects.create(
        school=school,
        code="G7",
        name="Grade 7",
        education_level=Grade.EducationLevel.JUNIOR_SCHOOL,
        order=7,
    )
    label = StreamLabel.objects.create(school=school, code="E", name="East")
    protected_stream = Stream.objects.create(school=school, grade=grade, code="E", name="East")
    AttendanceRegister.objects.create(
        school=school,
        attendance_date=date(2026, 6, 28),
        session=AttendanceRegister.Session.MORNING,
        subject_type=AttendanceRegister.SubjectType.LEARNER,
        stream=protected_stream,
    )

    response = client.post(
        reverse("academics:delete_stream_label", kwargs={"label_id": label.id}),
        HTTP_HOST=f"{school.slug}.localhost",
        follow=True,
    )

    protected_stream.refresh_from_db()
    content = response.content.decode()
    assert response.status_code == 200
    assert not StreamLabel.objects.for_school(school).filter(id=label.id).exists()
    assert protected_stream.is_active is False
    assert "East stream archived." in content
    assert "Grade 7 East" not in content
