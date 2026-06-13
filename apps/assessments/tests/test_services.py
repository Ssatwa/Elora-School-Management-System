from datetime import date

import pytest
from django.core.exceptions import PermissionDenied, ValidationError

from apps.accounts.models import AuditLog
from apps.assessments.models import (
    Assessment,
    AssessmentWorkflowEvent,
    RatingLevel,
    Rubric,
    RubricCriterion,
)
from apps.assessments.services import (
    approve_assessment,
    moderate_assessment,
    record_result,
    submit_assessment,
)
from apps.assessments.tests.test_models import make_context, make_learner, make_outcome
from apps.learners.models import Enrollment
from tests.factories import MembershipFactory, SchoolFactory

pytestmark = pytest.mark.django_db


def setup_assessment():
    school = SchoolFactory()
    year, term, grade, stream, area, teacher = make_context(school)
    rubric = Rubric.objects.create(
        school=school,
        name="Numbers rubric",
        learning_area=area,
        grade=grade,
    )
    criterion = RubricCriterion.objects.create(
        school=school,
        rubric=rubric,
        outcome=make_outcome(school, grade, area),
        name="Number representation",
        sequence=1,
    )
    meeting = RatingLevel.objects.create(
        school=school,
        code="ME",
        name="Meeting Expectation",
        rank=3,
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
        status=Assessment.Status.OPEN,
    )
    return school, year, stream, teacher, assessment, criterion, meeting


def enroll(school, learner, year, stream):
    return Enrollment.objects.create(
        school=school,
        learner=learner,
        academic_year=year,
        grade=stream.grade,
        stream=stream,
        start_date=date(2026, 1, 6),
    )


def test_assigned_teacher_records_complete_result_and_evidence():
    school, year, stream, teacher, assessment, criterion, meeting = setup_assessment()
    learner = make_learner(school)
    enroll(school, learner, year, stream)

    result = record_result(
        school=school,
        actor=teacher.membership.user,
        assessment=assessment,
        learner=learner,
        overall_rating=meeting,
        teacher_comment="Consistently represents whole numbers.",
        criterion_ratings=[{"criterion": criterion, "rating": meeting, "comment": "Secure"}],
        evidence=[
            {
                "outcome": criterion.outcome,
                "title": "Workbook page",
                "file_name": "workbook.pdf",
                "content_type": "application/pdf",
                "size_bytes": 500,
            }
        ],
    )

    assert result.is_complete is True
    assert result.criterion_ratings.get().rating == meeting
    assert result.evidence.get().title == "Workbook page"
    assert AuditLog.objects.filter(action="assessments.result.recorded").count() == 1


def test_non_assigned_teacher_cannot_record_result():
    school, year, stream, teacher, assessment, criterion, meeting = setup_assessment()
    learner = make_learner(school)
    enroll(school, learner, year, stream)
    other = MembershipFactory(school=school, role_code="teacher").user

    with pytest.raises(PermissionDenied):
        record_result(
            school=school,
            actor=other,
            assessment=assessment,
            learner=learner,
            overall_rating=meeting,
            teacher_comment="",
            criterion_ratings=[{"criterion": criterion, "rating": meeting}],
            evidence=[],
        )


def test_submission_requires_every_active_learner_and_criterion():
    school, year, stream, teacher, assessment, criterion, meeting = setup_assessment()
    first = make_learner(school)
    second = make_learner(school, "2026-0002")
    enroll(school, first, year, stream)
    enroll(school, second, year, stream)
    record_result(
        school=school,
        actor=teacher.membership.user,
        assessment=assessment,
        learner=first,
        overall_rating=meeting,
        teacher_comment="Ready",
        criterion_ratings=[{"criterion": criterion, "rating": meeting}],
        evidence=[],
    )

    with pytest.raises(ValidationError, match="active learner"):
        submit_assessment(
            school=school,
            actor=teacher.membership.user,
            assessment=assessment,
        )

    assessment.refresh_from_db()
    assert assessment.status == Assessment.Status.OPEN


def test_department_head_moderates_and_principal_approves_in_order():
    school, year, stream, teacher, assessment, criterion, meeting = setup_assessment()
    learner = make_learner(school)
    enroll(school, learner, year, stream)
    record_result(
        school=school,
        actor=teacher.membership.user,
        assessment=assessment,
        learner=learner,
        overall_rating=meeting,
        teacher_comment="Ready",
        criterion_ratings=[{"criterion": criterion, "rating": meeting}],
        evidence=[],
    )
    submit_assessment(
        school=school,
        actor=teacher.membership.user,
        assessment=assessment,
    )
    department_head = MembershipFactory(
        school=school,
        role_code="department_head",
    ).user
    principal = MembershipFactory(school=school, role_code="principal").user

    moderate_assessment(
        school=school,
        actor=department_head,
        assessment=assessment,
        comment="Evidence and ratings sampled.",
    )
    approved = approve_assessment(
        school=school,
        actor=principal,
        assessment=assessment,
        comment="Approved for reporting.",
    )

    assert approved.status == Assessment.Status.APPROVED
    assert AssessmentWorkflowEvent.objects.filter(assessment=assessment).count() == 3
    assert AuditLog.objects.filter(action="assessments.assessment.approved").count() == 1


def test_principal_cannot_approve_unmoderated_assessment():
    school, year, stream, teacher, assessment, criterion, meeting = setup_assessment()
    principal = MembershipFactory(school=school, role_code="principal").user

    with pytest.raises(ValidationError, match="moderated"):
        approve_assessment(
            school=school,
            actor=principal,
            assessment=assessment,
            comment="Too early",
        )
