from datetime import date

import pytest
from django.core.exceptions import ValidationError

from apps.assessments.models import (
    Assessment,
    RatingLevel,
    Rubric,
    RubricCriterion,
)
from apps.assessments.services import record_result
from apps.assessments.tests.test_models import make_context, make_learner, make_outcome
from apps.attendance.models import AttendanceRegister, LearnerAttendanceEntry
from apps.attendance.services import mark_learner_attendance
from apps.learners.models import Enrollment
from apps.reports.models import ReportCard, ReportGenerationJob
from apps.reports.services import (
    create_report_snapshot,
    generate_report_pdf,
    publish_report,
)
from tests.factories import MembershipFactory, SchoolFactory

pytestmark = pytest.mark.django_db


def setup_approved_result():
    school = SchoolFactory()
    year, term, grade, stream, area, teacher = make_context(school)
    learner = make_learner(school)
    Enrollment.objects.create(
        school=school,
        learner=learner,
        academic_year=year,
        grade=grade,
        stream=stream,
        start_date=date(2026, 1, 6),
    )
    outcome = make_outcome(school, grade, area)
    rubric = Rubric.objects.create(
        school=school,
        name="Numbers rubric",
        learning_area=area,
        grade=grade,
    )
    criterion = RubricCriterion.objects.create(
        school=school,
        rubric=rubric,
        outcome=outcome,
        name="Number representation",
        sequence=1,
    )
    rating = RatingLevel.objects.create(
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
    record_result(
        school=school,
        actor=teacher.membership.user,
        assessment=assessment,
        learner=learner,
        overall_rating=rating,
        teacher_comment="Secure understanding.",
        criterion_ratings=[{"criterion": criterion, "rating": rating}],
        evidence=[],
    )
    assessment.status = Assessment.Status.APPROVED
    assessment.save(update_fields=["status"])
    mark_learner_attendance(
        school=school,
        actor=teacher.membership.user,
        attendance_date=date(2026, 6, 13),
        session=AttendanceRegister.Session.MORNING,
        stream=stream,
        rows=[{"learner": learner, "status": LearnerAttendanceEntry.Status.PRESENT}],
    )
    return school, term, learner


def test_report_snapshot_contains_approved_results_and_attendance():
    school, term, learner = setup_approved_result()

    report = create_report_snapshot(
        school=school,
        actor=MembershipFactory(school=school, role_code="principal").user,
        learner=learner,
        term=term,
        principal_remark="A strong term.",
    )

    assert report.snapshot["learner"]["admission_number"] == learner.admission_number
    assert report.snapshot["assessments"][0]["overall_rating"] == "ME"
    assert report.snapshot["attendance"]["present"] == 1
    assert report.snapshot_hash


def test_report_snapshot_is_immutable_after_creation():
    school, term, learner = setup_approved_result()
    report = create_report_snapshot(
        school=school,
        actor=MembershipFactory(school=school, role_code="principal").user,
        learner=learner,
        term=term,
        principal_remark="A strong term.",
    )
    report.snapshot = {"changed": True}

    with pytest.raises(ValidationError, match="immutable"):
        report.save()


def test_generate_report_pdf_is_valid_and_idempotent():
    school, term, learner = setup_approved_result()
    report = create_report_snapshot(
        school=school,
        actor=MembershipFactory(school=school, role_code="principal").user,
        learner=learner,
        term=term,
        principal_remark="A strong term.",
    )

    first = generate_report_pdf(report_id=report.id, school_id=school.id)
    second = generate_report_pdf(report_id=report.id, school_id=school.id)

    report.refresh_from_db()
    assert first == second
    assert report.status == ReportCard.Status.READY
    assert report.pdf_checksum == first
    assert report.pdf.read().startswith(b"%PDF")
    assert ReportGenerationJob.objects.filter(report=report).count() == 1


def test_publish_requires_generated_pdf_and_principal_role():
    school, term, learner = setup_approved_result()
    report = create_report_snapshot(
        school=school,
        actor=MembershipFactory(school=school, role_code="principal").user,
        learner=learner,
        term=term,
        principal_remark="A strong term.",
    )
    principal = MembershipFactory(school=school, role_code="principal").user

    with pytest.raises(ValidationError, match="generated"):
        publish_report(school=school, actor=principal, report=report)

    generate_report_pdf(report_id=report.id, school_id=school.id)
    published = publish_report(school=school, actor=principal, report=report)

    assert published.status == ReportCard.Status.PUBLISHED
    assert published.published_at is not None
