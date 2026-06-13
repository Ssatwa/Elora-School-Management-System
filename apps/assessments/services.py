from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from apps.accounts.audit import record_audit_event
from apps.assessments.models import (
    Assessment,
    AssessmentResult,
    AssessmentWorkflowEvent,
    CriterionRating,
    Evidence,
)
from apps.assessments.permissions import (
    can_approve_assessment,
    can_enter_assessment,
    can_moderate_assessment,
)
from apps.learners.models import Enrollment


def _require_school(school, **values):
    for label, value in values.items():
        if value.school_id != school.id:
            raise ValidationError(
                f"{label.replace('_', ' ').title()} must belong to the same school."
            )


def _record_transition(*, school, assessment, actor, action, from_status, to_status, comment):
    AssessmentWorkflowEvent.objects.create(
        school=school,
        assessment=assessment,
        actor=actor,
        action=action,
        from_status=from_status,
        to_status=to_status,
        comment=comment,
    )
    record_audit_event(
        school=school,
        actor=actor,
        action=f"assessments.assessment.{action}",
        target_type="assessments.Assessment",
        target_id=assessment.id,
        metadata={
            "from_status": from_status,
            "to_status": to_status,
            "comment": comment,
        },
    )


@transaction.atomic
def record_result(
    *,
    school,
    actor,
    assessment,
    learner,
    overall_rating,
    teacher_comment,
    criterion_ratings,
    evidence,
):
    _require_school(
        school,
        assessment=assessment,
        learner=learner,
        overall_rating=overall_rating,
    )
    locked = Assessment.objects.select_for_update().select_related(
        "teacher__membership"
    ).get(pk=assessment.pk)
    if not can_enter_assessment(actor, school, locked):
        raise PermissionDenied("Only the assigned teacher can record this assessment.")
    if locked.status not in (Assessment.Status.DRAFT, Assessment.Status.OPEN):
        raise ValidationError("Results can only be entered while an assessment is open.")

    active_enrollment = Enrollment.objects.for_school(school).filter(
        learner=learner,
        stream=locked.stream,
        academic_year=locked.term.academic_year,
        status=Enrollment.Status.ACTIVE,
    )
    if not active_enrollment.exists():
        raise ValidationError("Learner must have an active enrollment in this stream.")

    expected_criteria = set(locked.rubric.criteria.values_list("id", flat=True))
    supplied_criteria = {item["criterion"].id for item in criterion_ratings}
    if supplied_criteria != expected_criteria:
        raise ValidationError("Every rubric criterion requires exactly one rating.")

    result, _ = AssessmentResult.objects.update_or_create(
        school=school,
        assessment=locked,
        learner=learner,
        defaults={
            "overall_rating": overall_rating,
            "teacher_comment": teacher_comment,
            "is_complete": True,
        },
    )
    result.full_clean()
    result.save()
    result.criterion_ratings.all().delete()
    for item in criterion_ratings:
        criterion = item["criterion"]
        rating = item["rating"]
        _require_school(school, criterion=criterion, rating=rating)
        row = CriterionRating(
            school=school,
            result=result,
            criterion=criterion,
            rating=rating,
            comment=item.get("comment", ""),
        )
        row.full_clean()
        row.save()
    for item in evidence:
        values = dict(item)
        outcome = values.pop("outcome")
        _require_school(school, outcome=outcome)
        row = Evidence(
            school=school,
            result=result,
            learner=learner,
            outcome=outcome,
            **values,
        )
        row.full_clean()
        row.save()

    record_audit_event(
        school=school,
        actor=actor,
        action="assessments.result.recorded",
        target_type="assessments.AssessmentResult",
        target_id=result.id,
        metadata={
            "assessment_id": str(locked.id),
            "learner_id": str(learner.id),
            "criterion_count": len(criterion_ratings),
            "evidence_count": len(evidence),
        },
    )
    return result


@transaction.atomic
def submit_assessment(*, school, actor, assessment, comment=""):
    locked = Assessment.objects.select_for_update().select_related(
        "teacher__membership", "term", "stream", "rubric"
    ).get(pk=assessment.pk)
    if not can_enter_assessment(actor, school, locked):
        raise PermissionDenied("Only the assigned teacher can submit this assessment.")
    if locked.status not in (Assessment.Status.DRAFT, Assessment.Status.OPEN):
        raise ValidationError("Only an open assessment can be submitted.")

    learner_ids = set(
        Enrollment.objects.for_school(school)
        .filter(
            stream=locked.stream,
            academic_year=locked.term.academic_year,
            status=Enrollment.Status.ACTIVE,
        )
        .values_list("learner_id", flat=True)
    )
    complete_ids = set(
        AssessmentResult.objects.for_school(school)
        .filter(
            assessment=locked,
            learner_id__in=learner_ids,
            is_complete=True,
        )
        .values_list("learner_id", flat=True)
    )
    if complete_ids != learner_ids:
        raise ValidationError("Every active learner requires a complete result.")
    criterion_count = locked.rubric.criteria.count()
    for result in locked.results.filter(learner_id__in=learner_ids):
        if result.criterion_ratings.count() != criterion_count:
            raise ValidationError("Every result requires all rubric criterion ratings.")

    previous = locked.status
    locked.status = Assessment.Status.SUBMITTED
    locked.submitted_at = timezone.now()
    locked.save(update_fields=["status", "submitted_at", "updated_at"])
    _record_transition(
        school=school,
        assessment=locked,
        actor=actor,
        action="submitted",
        from_status=previous,
        to_status=locked.status,
        comment=comment,
    )
    return locked


@transaction.atomic
def moderate_assessment(*, school, actor, assessment, comment):
    if not can_moderate_assessment(actor, school):
        raise PermissionDenied("Department Head permission is required.")
    locked = Assessment.objects.select_for_update().get(pk=assessment.pk)
    if locked.school_id != school.id:
        raise ValidationError("Assessment must belong to the same school.")
    if locked.status != Assessment.Status.SUBMITTED:
        raise ValidationError("Only a submitted assessment can be moderated.")
    previous = locked.status
    locked.status = Assessment.Status.MODERATED
    locked.moderated_at = timezone.now()
    locked.save(update_fields=["status", "moderated_at", "updated_at"])
    _record_transition(
        school=school,
        assessment=locked,
        actor=actor,
        action="moderated",
        from_status=previous,
        to_status=locked.status,
        comment=comment,
    )
    return locked


@transaction.atomic
def approve_assessment(*, school, actor, assessment, comment):
    if not can_approve_assessment(actor, school):
        raise PermissionDenied("Principal permission is required.")
    locked = Assessment.objects.select_for_update().get(pk=assessment.pk)
    if locked.school_id != school.id:
        raise ValidationError("Assessment must belong to the same school.")
    if locked.status != Assessment.Status.MODERATED:
        raise ValidationError("Only a moderated assessment can be approved.")
    previous = locked.status
    locked.status = Assessment.Status.APPROVED
    locked.approved_at = timezone.now()
    locked.save(update_fields=["status", "approved_at", "updated_at"])
    _record_transition(
        school=school,
        assessment=locked,
        actor=actor,
        action="approved",
        from_status=previous,
        to_status=locked.status,
        comment=comment,
    )
    return locked
