from typing import cast

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from apps.academics.models import (
    Competency,
    Grade,
    LearningArea,
    LearningOutcome,
    OutcomeCompetency,
    Strand,
    SubStrand,
)
from apps.tenancy.models import School
from tests.factories import SchoolFactory

pytestmark = pytest.mark.django_db


def create_curriculum_path(school):
    grade = Grade.objects.create(
        school=school,
        code="G7",
        name="Grade 7",
        education_level=Grade.EducationLevel.JUNIOR_SCHOOL,
        order=7,
    )
    learning_area = LearningArea.objects.create(
        school=school,
        code="MATH",
        name="Mathematics",
    )
    strand = Strand.objects.create(
        school=school,
        learning_area=learning_area,
        grade=grade,
        code="NUM",
        name="Numbers",
    )
    sub_strand = SubStrand.objects.create(
        school=school,
        strand=strand,
        code="WHOLE",
        name="Whole Numbers",
    )
    outcome = LearningOutcome.objects.create(
        school=school,
        sub_strand=sub_strand,
        code="MATH-G7-NUM-01",
        description="Represent and compare whole numbers.",
    )
    return grade, learning_area, strand, sub_strand, outcome


def test_curriculum_codes_are_unique_per_school():
    school = cast(School, SchoolFactory())
    LearningArea.objects.create(school=school, code="MATH", name="Mathematics")

    with pytest.raises(IntegrityError):
        LearningArea.objects.create(school=school, code="MATH", name="Numeracy")


def test_strand_rejects_cross_school_learning_area():
    first_school = cast(School, SchoolFactory())
    second_school = cast(School, SchoolFactory())
    grade = Grade.objects.create(
        school=second_school,
        code="G7",
        name="Grade 7",
        education_level=Grade.EducationLevel.JUNIOR_SCHOOL,
        order=7,
    )
    learning_area = LearningArea.objects.create(
        school=first_school,
        code="MATH",
        name="Mathematics",
    )
    strand = Strand(
        school=second_school,
        learning_area=learning_area,
        grade=grade,
        code="NUM",
        name="Numbers",
    )

    with pytest.raises(ValidationError, match="same school"):
        strand.full_clean()


def test_curriculum_path_and_competency_link_are_school_scoped():
    school = cast(School, SchoolFactory())
    *_, outcome = create_curriculum_path(school)
    competency = Competency.objects.create(
        school=school,
        code="CTPS",
        name="Critical Thinking and Problem Solving",
    )
    link = OutcomeCompetency(
        school=school,
        outcome=outcome,
        competency=competency,
    )
    link.full_clean()
    link.save()

    assert outcome.competencies.get() == competency
    assert LearningOutcome.objects.for_school(school).get() == outcome


def test_outcome_competency_rejects_cross_school_links():
    first_school = cast(School, SchoolFactory())
    second_school = cast(School, SchoolFactory())
    *_, outcome = create_curriculum_path(first_school)
    competency = Competency.objects.create(
        school=second_school,
        code="CTPS",
        name="Critical Thinking and Problem Solving",
    )
    link = OutcomeCompetency(
        school=first_school,
        outcome=outcome,
        competency=competency,
    )

    with pytest.raises(ValidationError, match="same school"):
        link.full_clean()
