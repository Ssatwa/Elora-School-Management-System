from datetime import date, time

import pytest
from django.core.exceptions import ValidationError

from apps.academics.models import AcademicYear
from apps.accounts.models import AuditLog
from apps.attendance.models import (
    AbsenceAlert,
    AttendanceCorrection,
    AttendanceRegister,
    LearnerAttendanceEntry,
    StaffAttendanceEntry,
)
from apps.attendance.services import (
    attendance_summary,
    correct_attendance,
    mark_learner_attendance,
    mark_staff_attendance,
)
from apps.attendance.tests.test_models import (
    make_learner,
    make_stream,
    make_teacher,
)
from apps.learners.models import Enrollment
from tests.factories import SchoolFactory, UserFactory

pytestmark = pytest.mark.django_db


def enroll(learner, stream):
    academic_year = AcademicYear.objects.create(
        school=learner.school,
        name="2026",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
        status=AcademicYear.Status.ACTIVE,
    )
    return Enrollment.objects.create(
        school=learner.school,
        learner=learner,
        academic_year=academic_year,
        grade=stream.grade,
        stream=stream,
        start_date=date(2026, 1, 6),
    )


def test_bulk_learner_marking_completes_register_and_creates_absence_alert():
    school = SchoolFactory()
    actor = UserFactory()
    stream = make_stream(school)
    first = make_learner(school)
    second = make_learner(school, "2026-0002")
    enroll(first, stream)
    Enrollment.objects.create(
        school=school,
        learner=second,
        academic_year=first.enrollments.get().academic_year,
        grade=stream.grade,
        stream=stream,
        start_date=date(2026, 1, 6),
    )

    register = mark_learner_attendance(
        school=school,
        actor=actor,
        attendance_date=date(2026, 6, 13),
        session=AttendanceRegister.Session.MORNING,
        stream=stream,
        rows=[
            {"learner": first, "status": LearnerAttendanceEntry.Status.PRESENT},
            {
                "learner": second,
                "status": LearnerAttendanceEntry.Status.ABSENT,
                "note": "Guardian not reached",
            },
        ],
    )

    assert register.status == AttendanceRegister.Status.COMPLETED
    assert register.learner_entries.count() == 2
    assert AbsenceAlert.objects.for_school(school).filter(learner_entry__learner=second).exists()
    assert AuditLog.objects.filter(action="attendance.learner_register.completed").count() == 1


def test_bulk_marking_rolls_back_entire_register_for_invalid_learner():
    school = SchoolFactory()
    other = SchoolFactory(slug="other-attendance-service")
    stream = make_stream(school)
    learner = make_learner(other)

    with pytest.raises(ValidationError, match="same school"):
        mark_learner_attendance(
            school=school,
            actor=UserFactory(),
            attendance_date=date(2026, 6, 13),
            session=AttendanceRegister.Session.MORNING,
            stream=stream,
            rows=[{"learner": learner, "status": LearnerAttendanceEntry.Status.PRESENT}],
        )

    assert AttendanceRegister.objects.for_school(school).count() == 0


def test_staff_marking_prevents_duplicate_daily_register():
    school = SchoolFactory()
    actor = UserFactory()
    teacher = make_teacher(school)
    kwargs = {
        "school": school,
        "actor": actor,
        "attendance_date": date(2026, 6, 13),
        "session": AttendanceRegister.Session.MORNING,
        "rows": [{"teacher": teacher, "status": StaffAttendanceEntry.Status.PRESENT}],
    }
    mark_staff_attendance(**kwargs)

    with pytest.raises(ValidationError, match="already exists"):
        mark_staff_attendance(**kwargs)


def test_correction_updates_entry_and_preserves_immutable_history():
    school = SchoolFactory()
    actor = UserFactory()
    teacher = make_teacher(school)
    register = mark_staff_attendance(
        school=school,
        actor=actor,
        attendance_date=date(2026, 6, 13),
        session=AttendanceRegister.Session.MORNING,
        rows=[{"teacher": teacher, "status": StaffAttendanceEntry.Status.ABSENT}],
    )
    entry = register.staff_entries.get()

    correction = correct_attendance(
        school=school,
        actor=actor,
        entry=entry,
        new_status=StaffAttendanceEntry.Status.LATE,
        new_arrival_time=time(8, 12),
        new_note="Signed in at reception",
        reason="Biometric terminal was offline",
    )

    entry.refresh_from_db()
    assert entry.status == StaffAttendanceEntry.Status.LATE
    assert correction.old_status == StaffAttendanceEntry.Status.ABSENT
    assert correction.new_status == StaffAttendanceEntry.Status.LATE
    assert AttendanceCorrection.objects.for_school(school).count() == 1
    assert not AbsenceAlert.objects.for_school(school).filter(staff_entry=entry).exists()
    assert AuditLog.objects.filter(action="attendance.entry.corrected").count() == 1


def test_attendance_summary_counts_statuses_for_one_school():
    school = SchoolFactory()
    stream = make_stream(school)
    first = make_learner(school)
    second = make_learner(school, "2026-0002")
    mark_learner_attendance(
        school=school,
        actor=UserFactory(),
        attendance_date=date(2026, 6, 13),
        session=AttendanceRegister.Session.MORNING,
        stream=stream,
        rows=[
            {"learner": first, "status": LearnerAttendanceEntry.Status.PRESENT},
            {"learner": second, "status": LearnerAttendanceEntry.Status.ABSENT},
        ],
    )

    summary = attendance_summary(
        school=school,
        start_date=date(2026, 6, 13),
        end_date=date(2026, 6, 13),
        subject_type=AttendanceRegister.SubjectType.LEARNER,
    )

    assert summary["total"] == 2
    assert summary["present"] == 1
    assert summary["absent"] == 1
    assert summary["attendance_rate"] == 50.0
