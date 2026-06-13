from datetime import date

import pytest

from apps.attendance.exports import attendance_csv
from apps.attendance.models import AttendanceRegister, LearnerAttendanceEntry
from apps.attendance.services import mark_learner_attendance
from apps.attendance.tests.test_models import make_learner, make_stream
from tests.factories import SchoolFactory, UserFactory

pytestmark = pytest.mark.django_db


def test_attendance_csv_only_contains_requested_school_records():
    first = SchoolFactory()
    second = SchoolFactory(slug="second-export")
    for school, admission_number in ((first, "FIRST-001"), (second, "SECOND-001")):
        mark_learner_attendance(
            school=school,
            actor=UserFactory(),
            attendance_date=date(2026, 6, 13),
            session=AttendanceRegister.Session.MORNING,
            stream=make_stream(school, school.slug),
            rows=[
                {
                    "learner": make_learner(school, admission_number),
                    "status": LearnerAttendanceEntry.Status.PRESENT,
                }
            ],
        )

    content = attendance_csv(
        school=first,
        start_date=date(2026, 6, 1),
        end_date=date(2026, 6, 30),
    )

    assert "FIRST-001" in content
    assert "SECOND-001" not in content
    assert "attendance_date,session,subject_type" in content
