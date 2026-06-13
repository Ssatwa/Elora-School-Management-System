from datetime import date
from typing import cast

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from apps.academics.models import (
    AcademicYear,
    Grade,
    LearningArea,
    LearningOutcome,
    Strand,
    Stream,
    SubStrand,
    Term,
)
from apps.assessments.models import (
    Assessment,
    AssessmentResult,
    CriterionRating,
    Evidence,
    RatingLevel,
    Rubric,
    RubricCriterion,
)
from apps.learners.models import Learner
from apps.staff.models import TeacherProfile
from apps.tenancy.models import School
from tests.factories import MembershipFactory, SchoolFactory

pytestmark = pytest.mark.django_db


def make_context(school):
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
    grade = Grade.objects.create(
        school=school,
        code="G7",
        name="Grade 7",
        education_level=Grade.EducationLevel.JUNIOR_SCHOOL,
        order=7,
    )
    stream = Stream.objects.create(
        school=school,
        grade=grade,
        code="E",
        name="East",
    )
    area = LearningArea.objects.create(school=school, code="MATH", name="Mathematics")
    membership = MembershipFactory(school=school, role_code="teacher")
    teacher = TeacherProfile.objects.create(
        school=school,
        membership=membership,
        employee_number="T-001",
        employment_date=date(2024, 1, 8),
    )
    return year, term, grade, stream, area, teacher


def make_learner(school, number="2026-0001"):
    return Learner.objects.create(
        school=school,
        admission_number=number,
        first_name="Amina",
        last_name="Kamau",
        date_of_birth=date(2013, 6, 12),
        gender=Learner.Gender.FEMALE,
        admission_date=date(2026, 1, 6),
    )


def make_outcome(school, grade, area):
    strand = Strand.objects.create(
        school=school,
        learning_area=area,
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
    return LearningOutcome.objects.create(
        school=school,
        sub_strand=sub_strand,
        code="MATH-G7-01",
        description="Represent and compare whole numbers.",
    )


def test_rating_code_is_unique_per_school_and_ordered():
    school = cast(School, SchoolFactory())
    RatingLevel.objects.create(school=school, code="EE", name="Exceeding Expectation", rank=4)

    with pytest.raises(IntegrityError):
        RatingLevel.objects.create(
            school=school,
            code="EE",
            name="Duplicate",
            rank=3,
        )


def test_rubric_criterion_requires_outcome_from_same_school():
    first = cast(School, SchoolFactory())
    second = cast(School, SchoolFactory())
    _, _, grade, _, area, _ = make_context(first)
    other_year, other_term, other_grade, other_stream, other_area, other_teacher = (
        make_context(second)
    )
    rubric = Rubric.objects.create(
        school=first,
        name="Numbers rubric",
        learning_area=area,
        grade=grade,
    )
    criterion = RubricCriterion(
        school=first,
        rubric=rubric,
        outcome=make_outcome(second, other_grade, other_area),
        name="Number representation",
        sequence=1,
    )

    with pytest.raises(ValidationError, match="same school"):
        criterion.full_clean()


def test_assessment_requires_matching_term_stream_area_teacher_and_rubric():
    first = cast(School, SchoolFactory())
    second = cast(School, SchoolFactory())
    _, term, grade, stream, area, teacher = make_context(first)
    _, other_term, _, _, _, _ = make_context(second)
    rubric = Rubric.objects.create(
        school=first,
        name="Numbers rubric",
        learning_area=area,
        grade=grade,
    )
    assessment = Assessment(
        school=first,
        term=other_term,
        stream=stream,
        learning_area=area,
        teacher=teacher,
        rubric=rubric,
        title="Whole numbers check",
        assessment_type=Assessment.AssessmentType.FORMATIVE,
        assessment_date=date(2026, 6, 13),
    )

    with pytest.raises(ValidationError, match="same school"):
        assessment.full_clean()


def test_result_is_unique_per_assessment_and_learner():
    school = cast(School, SchoolFactory())
    _, term, grade, stream, area, teacher = make_context(school)
    rubric = Rubric.objects.create(
        school=school,
        name="Numbers rubric",
        learning_area=area,
        grade=grade,
    )
    assessment = Assessment.objects.create(
        school=school,
        term=term,
        stream=stream,
        learning_area=area,
        teacher=teacher,
        rubric=rubric,
        title="Whole numbers check",
        assessment_type=Assessment.AssessmentType.FORMATIVE,
        assessment_date=date(2026, 6, 13),
    )
    learner = make_learner(school)
    values = {"school": school, "assessment": assessment, "learner": learner}
    AssessmentResult.objects.create(**values)

    with pytest.raises(IntegrityError):
        AssessmentResult.objects.create(**values)


def test_criterion_rating_requires_result_criterion_and_rating_from_same_school():
    first = cast(School, SchoolFactory())
    second = cast(School, SchoolFactory())
    _, term, grade, stream, area, teacher = make_context(first)
    rubric = Rubric.objects.create(
        school=first,
        name="Numbers rubric",
        learning_area=area,
        grade=grade,
    )
    criterion = RubricCriterion.objects.create(
        school=first,
        rubric=rubric,
        outcome=make_outcome(first, grade, area),
        name="Number representation",
        sequence=1,
    )
    assessment = Assessment.objects.create(
        school=first,
        term=term,
        stream=stream,
        learning_area=area,
        teacher=teacher,
        rubric=rubric,
        title="Whole numbers check",
        assessment_type=Assessment.AssessmentType.FORMATIVE,
        assessment_date=date(2026, 6, 13),
    )
    result = AssessmentResult.objects.create(
        school=first,
        assessment=assessment,
        learner=make_learner(first),
    )
    rating = RatingLevel.objects.create(
        school=second,
        code="ME",
        name="Meeting Expectation",
        rank=3,
    )
    criterion_rating = CriterionRating(
        school=first,
        result=result,
        criterion=criterion,
        rating=rating,
    )

    with pytest.raises(ValidationError, match="same school"):
        criterion_rating.full_clean()


def test_evidence_requires_result_learner_and_outcome_alignment():
    school = cast(School, SchoolFactory())
    _, term, grade, stream, area, teacher = make_context(school)
    outcome = make_outcome(school, grade, area)
    rubric = Rubric.objects.create(
        school=school,
        name="Numbers rubric",
        learning_area=area,
        grade=grade,
    )
    assessment = Assessment.objects.create(
        school=school,
        term=term,
        stream=stream,
        learning_area=area,
        teacher=teacher,
        rubric=rubric,
        title="Whole numbers check",
        assessment_type=Assessment.AssessmentType.FORMATIVE,
        assessment_date=date(2026, 6, 13),
    )
    result = AssessmentResult.objects.create(
        school=school,
        assessment=assessment,
        learner=make_learner(school),
    )
    evidence = Evidence(
        school=school,
        result=result,
        learner=make_learner(school, "2026-0002"),
        outcome=outcome,
        title="Workbook page",
        file_name="workbook.pdf",
        content_type="application/pdf",
        size_bytes=100,
    )

    with pytest.raises(ValidationError, match="result learner"):
        evidence.full_clean()
