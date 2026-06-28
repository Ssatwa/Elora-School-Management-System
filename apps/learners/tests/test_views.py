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


def create_academic_context(school: School, grade_order=7, grade_name="Grade 7", stream_name="East"):
    year, _ = AcademicYear.objects.get_or_create(
        school=school,
        name="2026",
        defaults={
            "start_date": date(2026, 1, 1),
            "end_date": date(2026, 12, 31),
            "status": AcademicYear.Status.ACTIVE,
        },
    )
    grade = Grade.objects.create(
        school=school,
        code=f"G{grade_order}",
        name=grade_name,
        education_level=Grade.EducationLevel.JUNIOR_SCHOOL,
        order=grade_order,
    )
    stream = Stream.objects.create(
        school=school,
        grade=grade,
        code=stream_name[:1].upper(),
        name=stream_name,
    )
    return year, grade, stream


def create_learner(
    school: School,
    admission_number: str,
    first_name="Amina",
    last_name="Kamau",
    status=Learner.Status.ACTIVE,
):
    return Learner.objects.create(
        school=school,
        admission_number=admission_number,
        first_name=first_name,
        last_name=last_name,
        date_of_birth=date(2013, 6, 12),
        gender=Learner.Gender.FEMALE,
        admission_date=date(2026, 1, 6),
        status=status,
    )


def enroll(school: School, learner: Learner, year, grade, stream):
    return Enrollment.objects.create(
        school=school,
        learner=learner,
        academic_year=year,
        grade=grade,
        stream=stream,
        start_date=date(2026, 1, 6),
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
    assert "data-page-header" in content
    assert "data-record-table" in content
    assert "2026-0001" in content
    assert "SECRET-0001" not in content


def test_learner_index_defaults_to_grade_stream_and_name_order(client):
    school = cast(School, SchoolFactory())
    login_membership(client, school, "teacher")
    year, grade_one, blue = create_academic_context(
        school,
        grade_order=1,
        grade_name="Grade 1",
        stream_name="Blue",
    )
    _, grade_two, red = create_academic_context(
        school,
        grade_order=2,
        grade_name="Grade 2",
        stream_name="Red",
    )
    jane = create_learner(school, "2026-0002", first_name="Jane", last_name="Doe")
    amina = create_learner(school, "2026-0001", first_name="Amina", last_name="Kamau")
    mary = create_learner(school, "2026-0003", first_name="Mary", last_name="Wanjiku")
    enroll(school, jane, year, grade_one, blue)
    enroll(school, amina, year, grade_one, blue)
    enroll(school, mary, year, grade_two, red)

    response = client.get(reverse("learners:index"), HTTP_HOST=f"{school.slug}.localhost")
    content = response.content.decode()

    assert content.index("Amina Kamau") < content.index("Jane Doe")
    assert content.index("Jane Doe") < content.index("Mary Wanjiku")
    assert "Grade 1" in content
    assert "Blue" in content


def test_learner_index_filters_by_grade_stream_status_and_searches_placement(client):
    school = cast(School, SchoolFactory())
    login_membership(client, school, "teacher")
    year, grade_one, blue = create_academic_context(
        school,
        grade_order=1,
        grade_name="Grade 1",
        stream_name="Blue",
    )
    _, grade_two, red = create_academic_context(
        school,
        grade_order=2,
        grade_name="Grade 2",
        stream_name="Red",
    )
    amina = create_learner(school, "2026-0001", first_name="Amina", last_name="Kamau")
    mary = create_learner(
        school,
        "2026-0002",
        first_name="Mary",
        last_name="Wanjiku",
        status=Learner.Status.INACTIVE,
    )
    enroll(school, amina, year, grade_one, blue)
    enroll(school, mary, year, grade_two, red)

    filtered = client.get(
        reverse("learners:index"),
        {"grade": str(grade_one.id), "stream": str(blue.id), "status": Learner.Status.ACTIVE},
        HTTP_HOST=f"{school.slug}.localhost",
    ).content.decode()
    searched = client.get(
        reverse("learners:index"),
        {"q": "red"},
        HTTP_HOST=f"{school.slug}.localhost",
    ).content.decode()

    assert "Amina Kamau" in filtered
    assert "Mary Wanjiku" not in filtered
    assert "Mary Wanjiku" in searched
    assert "Amina Kamau" not in searched


def test_learner_index_sorts_by_selected_column_and_preserves_view_action(client):
    school = cast(School, SchoolFactory())
    login_membership(client, school, "teacher")
    create_learner(school, "2026-0002", first_name="Brian", last_name="Otieno")
    create_learner(school, "2026-0001", first_name="Amina", last_name="Kamau")

    response = client.get(
        reverse("learners:index"),
        {"sort": "admission", "direction": "asc"},
        HTTP_HOST=f"{school.slug}.localhost",
    )
    content = response.content.decode()

    assert content.index("2026-0001") < content.index("2026-0002")
    assert "View" in content
    assert "Unassigned" in content


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
    assert "data-empty-state" in response.content.decode()
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
