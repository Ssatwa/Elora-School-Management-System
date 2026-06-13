from datetime import date

import pytest

from apps.academics.models import LearningArea
from apps.accounts.models import AuditLog
from apps.attendance.exports import attendance_csv
from apps.attendance.models import AbsenceAlert, AttendanceRegister, LearnerAttendanceEntry
from apps.attendance.services import correct_attendance, mark_learner_attendance
from apps.attendance.tests.test_models import make_learner, make_stream, make_teacher
from apps.timetabling.models import Room, Timetable
from apps.timetabling.services import add_timetable_entry, publish_timetable
from apps.timetabling.tests.test_models import make_calendar, make_period
from tests.factories import SchoolFactory, UserFactory

pytestmark = pytest.mark.django_db


def test_milestone_three_exit_workflow():
    school = SchoolFactory()
    actor = UserFactory()
    year, term = make_calendar(school)
    timetable = Timetable.objects.create(
        school=school,
        academic_year=year,
        term=term,
        name="Operational timetable",
    )
    stream = make_stream(school)
    learner = make_learner(school)
    add_timetable_entry(
        school=school,
        actor=actor,
        timetable=timetable,
        period=make_period(school),
        stream=stream,
        learning_area=LearningArea.objects.create(
            school=school,
            code="math",
            name="Mathematics",
        ),
        teacher=make_teacher(school),
        room=Room.objects.create(school=school, code="R1", name="Room 1", capacity=40),
    )
    publish_timetable(school=school, actor=actor, timetable=timetable)

    register = mark_learner_attendance(
        school=school,
        actor=actor,
        attendance_date=date(2026, 6, 13),
        session=AttendanceRegister.Session.MORNING,
        stream=stream,
        rows=[{"learner": learner, "status": LearnerAttendanceEntry.Status.PRESENT}],
    )
    entry = register.learner_entries.get()
    correct_attendance(
        school=school,
        actor=actor,
        entry=entry,
        new_status=LearnerAttendanceEntry.Status.ABSENT,
        reason="Guardian confirmed illness",
        new_note="Sick at home",
    )
    export = attendance_csv(
        school=school,
        start_date=date(2026, 6, 13),
        end_date=date(2026, 6, 13),
    )

    timetable.refresh_from_db()
    assert timetable.status == Timetable.Status.PUBLISHED
    assert AbsenceAlert.objects.for_school(school).filter(learner_entry=entry).exists()
    assert "2026-0001" in export
    assert "absent" in export
    assert AuditLog.objects.filter(
        action__in=(
            "timetabling.timetable.published",
            "attendance.learner_register.completed",
            "attendance.entry.corrected",
        )
    ).count() == 3
