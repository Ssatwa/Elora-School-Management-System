from datetime import date

import pytest
from django.urls import reverse

from apps.academics.models import AcademicYear
from apps.attendance.models import AttendanceRegister, LearnerAttendanceEntry
from apps.attendance.tests.test_models import make_learner, make_stream
from apps.attendance.tests.test_models import make_teacher
from apps.learners.models import Enrollment
from tests.factories import MembershipFactory, SchoolFactory

pytestmark = pytest.mark.django_db


def login(client, school, role_code):
    membership = MembershipFactory(school=school, role_code=role_code)
    client.force_login(membership.user)
    return membership


def enroll(learner, stream):
    year = AcademicYear.objects.create(
        school=learner.school,
        name="2026",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
        status=AcademicYear.Status.ACTIVE,
    )
    return Enrollment.objects.create(
        school=learner.school,
        learner=learner,
        academic_year=year,
        grade=stream.grade,
        stream=stream,
        start_date=date(2026, 1, 6),
    )


def test_teacher_can_view_attendance_dashboard_but_parent_cannot(client):
    school = SchoolFactory()
    login(client, school, "teacher")
    response = client.get(
        reverse("attendance:index"),
        HTTP_HOST=f"{school.slug}.localhost",
    )
    assert response.status_code == 200
    assert "Attendance operations" in response.content.decode()

    parent_school = SchoolFactory(slug="parent-attendance")
    login(client, parent_school, "parent")
    denied = client.get(
        reverse("attendance:index"),
        HTTP_HOST=f"{parent_school.slug}.localhost",
    )
    assert denied.status_code == 403


def test_class_teacher_can_complete_bulk_learner_register(client):
    school = SchoolFactory()
    login(client, school, "class_teacher")
    stream = make_stream(school)
    first = make_learner(school)
    second = make_learner(school, "2026-0002")
    first_enrollment = enroll(first, stream)
    Enrollment.objects.create(
        school=school,
        learner=second,
        academic_year=first_enrollment.academic_year,
        grade=stream.grade,
        stream=stream,
        start_date=date(2026, 1, 6),
    )

    response = client.post(
        reverse("attendance:learner-register"),
        {
            "attendance_date": "2026-06-13",
            "session": AttendanceRegister.Session.MORNING,
            "stream": str(stream.id),
            f"status_{first.id}": LearnerAttendanceEntry.Status.PRESENT,
            f"status_{second.id}": LearnerAttendanceEntry.Status.ABSENT,
            f"note_{second.id}": "Reported sick",
        },
        HTTP_HOST=f"{school.slug}.localhost",
    )

    assert response.status_code == 302
    register = AttendanceRegister.objects.for_school(school).get()
    assert register.learner_entries.count() == 2


def test_attendance_dashboard_and_export_do_not_leak_other_school(client):
    school = SchoolFactory()
    other = SchoolFactory(slug="other-attendance-view")
    login(client, school, "principal")
    own_stream = make_stream(school)
    other_stream = make_stream(other, "-other")
    AttendanceRegister.objects.create(
        school=school,
        attendance_date=date(2026, 6, 13),
        session=AttendanceRegister.Session.MORNING,
        subject_type=AttendanceRegister.SubjectType.LEARNER,
        stream=own_stream,
    )
    AttendanceRegister.objects.create(
        school=other,
        attendance_date=date(2026, 6, 13),
        session=AttendanceRegister.Session.MORNING,
        subject_type=AttendanceRegister.SubjectType.LEARNER,
        stream=other_stream,
    )

    response = client.get(
        reverse("attendance:index"),
        HTTP_HOST=f"{school.slug}.localhost",
    )
    assert response.status_code == 200
    assert str(own_stream) in response.content.decode()
    assert str(other_stream) not in response.content.decode()

    exported = client.get(
        reverse("attendance:export"),
        {"start_date": "2026-06-01", "end_date": "2026-06-30"},
        HTTP_HOST=f"{school.slug}.localhost",
    )
    assert exported.status_code == 200
    assert exported["Content-Type"].startswith("text/csv")


def test_sidebar_shows_attendance_for_teacher(client):
    school = SchoolFactory()
    login(client, school, "teacher")

    response = client.get(
        reverse("attendance:index"),
        HTTP_HOST=f"{school.slug}.localhost",
    )

    assert "Attendance" in response.content.decode()


def test_principal_can_complete_bulk_staff_register(client):
    school = SchoolFactory()
    login(client, school, "principal")
    teacher = make_teacher(school)

    response = client.post(
        reverse("attendance:staff-register"),
        {
            "attendance_date": "2026-06-13",
            "session": AttendanceRegister.Session.MORNING,
            f"status_{teacher.id}": "late",
            f"arrival_time_{teacher.id}": "08:12",
        },
        HTTP_HOST=f"{school.slug}.localhost",
    )

    assert response.status_code == 302
    register = AttendanceRegister.objects.for_school(school).get(
        subject_type=AttendanceRegister.SubjectType.STAFF
    )
    assert register.staff_entries.get().status == "late"
