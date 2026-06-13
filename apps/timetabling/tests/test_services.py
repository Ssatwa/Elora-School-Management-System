from datetime import date

import pytest
from django.core.exceptions import ValidationError

from apps.academics.models import LearningArea
from apps.accounts.models import AuditLog
from apps.attendance.tests.test_models import make_stream, make_teacher
from apps.timetabling.models import Room, Timetable, TimetableEntry
from apps.timetabling.services import (
    add_timetable_entry,
    publish_timetable,
    validate_timetable,
)
from apps.timetabling.tests.test_models import make_calendar, make_period
from tests.factories import SchoolFactory, UserFactory

pytestmark = pytest.mark.django_db


def setup_timetable():
    school = SchoolFactory()
    year, term = make_calendar(school)
    return school, Timetable.objects.create(
        school=school,
        academic_year=year,
        term=term,
        name="Term 2 master",
    )


def make_area(school, code="math"):
    return LearningArea.objects.create(school=school, code=code, name=code.title())


def make_room(school, code="R1"):
    return Room.objects.create(school=school, code=code, name=f"Room {code}", capacity=40)


@pytest.mark.parametrize(
    ("field", "message"),
    [
        ("teacher", "Teacher conflict"),
        ("room", "Room conflict"),
        ("stream", "Stream conflict"),
    ],
)
def test_add_entry_rejects_period_conflicts(field, message):
    school, timetable = setup_timetable()
    period = make_period(school)
    first_values = {
        "stream": make_stream(school),
        "learning_area": make_area(school),
        "teacher": make_teacher(school),
        "room": make_room(school),
    }
    add_timetable_entry(
        school=school,
        actor=UserFactory(),
        timetable=timetable,
        period=period,
        **first_values,
    )
    second_values = {
        "stream": make_stream(school, "-b"),
        "learning_area": make_area(school, "english"),
        "teacher": make_teacher(school, "T-002"),
        "room": make_room(school, "R2"),
    }
    second_values[field] = first_values[field]

    with pytest.raises(ValidationError, match=message):
        add_timetable_entry(
            school=school,
            actor=UserFactory(),
            timetable=timetable,
            period=period,
            **second_values,
        )


def test_add_entry_rejects_duplicate_learning_area_for_stream_and_period():
    school, timetable = setup_timetable()
    period = make_period(school)
    stream = make_stream(school)
    area = make_area(school)
    add_timetable_entry(
        school=school,
        actor=UserFactory(),
        timetable=timetable,
        period=period,
        stream=stream,
        learning_area=area,
        teacher=make_teacher(school),
        room=make_room(school),
    )

    with pytest.raises(ValidationError, match="Learning area conflict"):
        add_timetable_entry(
            school=school,
            actor=UserFactory(),
            timetable=timetable,
            period=period,
            stream=stream,
            learning_area=area,
            teacher=make_teacher(school, "T-002"),
            room=make_room(school, "R2"),
        )


def test_publish_requires_entries_and_marks_conflict_free_timetable_published():
    school, empty = setup_timetable()
    with pytest.raises(ValidationError, match="at least one"):
        publish_timetable(school=school, actor=UserFactory(), timetable=empty)

    entry = TimetableEntry.objects.create(
        school=school,
        timetable=empty,
        period=make_period(school),
        stream=make_stream(school),
        learning_area=make_area(school),
        teacher=make_teacher(school),
        room=make_room(school),
    )
    assert validate_timetable(school=school, timetable=empty) == []

    published = publish_timetable(school=school, actor=UserFactory(), timetable=empty)

    assert published.status == Timetable.Status.PUBLISHED
    assert published.published_at is not None
    assert published.entries.get() == entry
    assert AuditLog.objects.filter(action="timetabling.timetable.published").count() == 1


def test_published_timetable_cannot_be_edited():
    school, timetable = setup_timetable()
    timetable.status = Timetable.Status.PUBLISHED
    timetable.save(update_fields=["status"])

    with pytest.raises(ValidationError, match="Draft timetables"):
        add_timetable_entry(
            school=school,
            actor=UserFactory(),
            timetable=timetable,
            period=make_period(school),
            stream=make_stream(school),
            learning_area=make_area(school),
            teacher=make_teacher(school),
            room=make_room(school),
        )
