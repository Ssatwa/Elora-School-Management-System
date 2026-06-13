from datetime import date

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from apps.academics.models import AcademicYear, Grade, Stream, Term
from tests.factories import SchoolFactory

pytestmark = pytest.mark.django_db


def test_academic_year_dates_must_be_ordered():
    year = AcademicYear(
        school=SchoolFactory(),
        name="2026",
        start_date=date(2026, 12, 31),
        end_date=date(2026, 1, 1),
    )

    with pytest.raises(ValidationError, match="end date"):
        year.full_clean()


def test_academic_year_name_is_unique_per_school():
    school = SchoolFactory()
    AcademicYear.objects.create(
        school=school,
        name="2026",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
    )

    with pytest.raises(IntegrityError):
        AcademicYear.objects.create(
            school=school,
            name="2026",
            start_date=date(2027, 1, 1),
            end_date=date(2027, 12, 31),
        )


def test_term_must_fit_inside_academic_year():
    school = SchoolFactory()
    year = AcademicYear.objects.create(
        school=school,
        name="2026",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
    )
    term = Term(
        school=school,
        academic_year=year,
        name="Term 1",
        sequence=1,
        start_date=date(2025, 12, 1),
        end_date=date(2026, 4, 1),
    )

    with pytest.raises(ValidationError, match="academic year"):
        term.full_clean()


def test_stream_requires_grade_from_same_school():
    first_school = SchoolFactory()
    second_school = SchoolFactory()
    grade = Grade.objects.create(
        school=first_school,
        code="G7",
        name="Grade 7",
        education_level=Grade.EducationLevel.JUNIOR_SCHOOL,
        order=7,
    )
    stream = Stream(
        school=second_school,
        grade=grade,
        code="E",
        name="East",
    )

    with pytest.raises(ValidationError, match="same school"):
        stream.full_clean()


def test_academic_models_are_explicitly_scoped_by_school():
    first_school = SchoolFactory()
    second_school = SchoolFactory()
    Grade.objects.create(
        school=first_school,
        code="G7",
        name="Grade 7",
        education_level=Grade.EducationLevel.JUNIOR_SCHOOL,
        order=7,
    )
    Grade.objects.create(
        school=second_school,
        code="G7",
        name="Grade 7",
        education_level=Grade.EducationLevel.JUNIOR_SCHOOL,
        order=7,
    )

    assert Grade.objects.for_school(first_school).count() == 1
    assert Grade.objects.for_school(second_school).count() == 1
