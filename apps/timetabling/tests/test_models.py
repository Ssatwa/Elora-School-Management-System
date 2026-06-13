from datetime import date, time
from typing import cast

import pytest
from django.core.exceptions import ValidationError

from apps.academics.models import AcademicYear, LearningArea, Term
from apps.attendance.tests.test_models import make_stream, make_teacher
from apps.tenancy.models import School
from apps.timetabling.models import (
    Room,
    Timetable,
    TimetableEntry,
    TimetablePeriod,
)
from tests.factories import SchoolFactory

pytestmark = pytest.mark.django_db


def make_calendar(school):
    year = AcademicYear.objects.create(
        school=school,
        name="2026",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
        status=AcademicYear.Status.ACTIVE,
    )
    term = Term.objects.create(
        school=school,
        academic_year=year,
        name="Term 2",
        sequence=2,
        start_date=date(2026, 5, 1),
        end_date=date(2026, 8, 15),
    )
    return year, term


def make_period(school, sequence=1):
    return TimetablePeriod.objects.create(
        school=school,
        weekday=TimetablePeriod.Weekday.MONDAY,
        sequence=sequence,
        name=f"Lesson {sequence}",
        start_time=time(8 + sequence - 1, 0),
        end_time=time(8 + sequence - 1, 40),
    )


def test_period_requires_end_time_after_start_time():
    school = cast(School, SchoolFactory())
    period = TimetablePeriod(
        school=school,
        weekday=TimetablePeriod.Weekday.MONDAY,
        sequence=1,
        name="Lesson 1",
        start_time=time(9, 0),
        end_time=time(8, 40),
    )

    with pytest.raises(ValidationError, match="after"):
        period.full_clean()


def test_timetable_term_and_year_must_belong_to_same_school_and_match():
    first = cast(School, SchoolFactory())
    second = cast(School, SchoolFactory(slug="second-timetable"))
    year, _ = make_calendar(first)
    _, other_term = make_calendar(second)
    timetable = Timetable(
        school=first,
        academic_year=year,
        term=other_term,
        name="Term 2 master",
    )

    with pytest.raises(ValidationError, match="same school"):
        timetable.full_clean()


def test_entry_requires_all_references_from_timetable_school():
    first = cast(School, SchoolFactory())
    second = cast(School, SchoolFactory(slug="second-entry-timetable"))
    year, term = make_calendar(first)
    timetable = Timetable.objects.create(
        school=first,
        academic_year=year,
        term=term,
        name="Term 2 master",
    )
    entry = TimetableEntry(
        school=first,
        timetable=timetable,
        period=make_period(first),
        stream=make_stream(first),
        learning_area=LearningArea.objects.create(
            school=first,
            code="math",
            name="Mathematics",
        ),
        teacher=make_teacher(second),
        room=Room.objects.create(school=first, code="R1", name="Room 1", capacity=40),
    )

    with pytest.raises(ValidationError, match="same school"):
        entry.full_clean()
