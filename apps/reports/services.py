import hashlib
import json

from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models import Count
from django.utils import timezone

from apps.accounts.audit import record_audit_event
from apps.accounts.permissions import has_school_role
from apps.assessments.models import Assessment, AssessmentResult
from apps.attendance.models import LearnerAttendanceEntry
from apps.reports.models import ReportCard, ReportGenerationJob
from apps.reports.pdf import render_report_card_pdf
from apps.tenancy.models import School


def _snapshot_hash(snapshot):
    encoded = json.dumps(snapshot, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _attendance_snapshot(*, school, learner, term):
    counts = {
        item["status"]: item["count"]
        for item in (
            LearnerAttendanceEntry.objects.for_school(school)
            .filter(
                learner=learner,
                register__attendance_date__range=(term.start_date, term.end_date),
            )
            .values("status")
            .annotate(count=Count("id"))
        )
    }
    total = sum(counts.values())
    present = counts.get(LearnerAttendanceEntry.Status.PRESENT, 0)
    return {
        "total": total,
        "present": present,
        "absent": counts.get(LearnerAttendanceEntry.Status.ABSENT, 0),
        "late": counts.get(LearnerAttendanceEntry.Status.LATE, 0),
        "excused": counts.get(LearnerAttendanceEntry.Status.EXCUSED, 0),
        "attendance_rate": round((present / total) * 100, 1) if total else 0.0,
    }


@transaction.atomic
def create_report_snapshot(*, school, actor, learner, term, principal_remark):
    if not has_school_role(actor, school, "principal", "school_admin"):
        raise PermissionDenied("Principal permission is required.")
    if learner.school_id != school.id or term.school_id != school.id:
        raise ValidationError("Learner and term must belong to the same school.")
    existing = ReportCard.objects.for_school(school).filter(
        learner=learner,
        term=term,
    ).first()
    if existing is not None:
        return existing

    results = (
        AssessmentResult.objects.for_school(school)
        .filter(
            learner=learner,
            assessment__term=term,
            assessment__status=Assessment.Status.APPROVED,
            is_complete=True,
        )
        .select_related(
            "assessment__learning_area",
            "overall_rating",
        )
        .prefetch_related(
            "criterion_ratings__criterion__outcome",
            "criterion_ratings__rating",
        )
    )
    assessment_rows = []
    for result in results:
        assessment_rows.append(
            {
                "assessment_id": str(result.assessment_id),
                "title": result.assessment.title,
                "type": result.assessment.assessment_type,
                "learning_area": result.assessment.learning_area.name,
                "overall_rating": result.overall_rating.code if result.overall_rating else "",
                "overall_rating_name": (
                    result.overall_rating.name if result.overall_rating else "Not rated"
                ),
                "teacher_comment": result.teacher_comment,
                "moderated_comment": result.moderated_comment,
                "criteria": [
                    {
                        "criterion": row.criterion.name,
                        "outcome": row.criterion.outcome.description,
                        "rating": row.rating.code,
                        "rating_name": row.rating.name,
                        "comment": row.comment,
                    }
                    for row in result.criterion_ratings.all()
                ],
            }
        )
    if not assessment_rows:
        raise ValidationError("At least one approved assessment result is required.")
    enrollment = (
        learner.enrollments.filter(academic_year=term.academic_year)
        .select_related("grade", "stream")
        .order_by("-start_date")
        .first()
    )
    class_name = (
        f"{enrollment.grade.name} {enrollment.stream.name}" if enrollment else "Not assigned"
    )
    snapshot = {
        "version": 1,
        "school": {"id": str(school.id), "name": school.name},
        "learner": {
            "id": str(learner.id),
            "name": learner.full_name,
            "admission_number": learner.admission_number,
            "class_name": class_name,
        },
        "term": {
            "id": str(term.id),
            "name": term.name,
            "academic_year": term.academic_year.name,
            "start_date": term.start_date.isoformat(),
            "end_date": term.end_date.isoformat(),
        },
        "assessments": assessment_rows,
        "attendance": _attendance_snapshot(
            school=school,
            learner=learner,
            term=term,
        ),
        "principal_remark": principal_remark,
        "generated_on": timezone.localdate().isoformat(),
    }
    report = ReportCard(
        school=school,
        learner=learner,
        term=term,
        snapshot=snapshot,
        snapshot_hash=_snapshot_hash(snapshot),
        principal_remark=principal_remark,
    )
    report.full_clean()
    report.save()
    ReportGenerationJob.objects.create(school=school, report=report)
    record_audit_event(
        school=school,
        actor=actor,
        action="reports.snapshot.created",
        target_type="reports.ReportCard",
        target_id=report.id,
        metadata={"learner_id": str(learner.id), "term_id": str(term.id)},
    )
    return report


@transaction.atomic
def generate_report_pdf(*, report_id, school_id):
    school = School.objects.get(pk=school_id, is_active=True)
    report = (
        ReportCard.objects.select_for_update()
        .for_school(school)
        .select_related("learner", "term")
        .get(pk=report_id)
    )
    job = ReportGenerationJob.objects.select_for_update().get(report=report)
    if report.pdf_checksum and report.pdf and report.status in (
        ReportCard.Status.READY,
        ReportCard.Status.PUBLISHED,
    ):
        return report.pdf_checksum
    job.status = ReportGenerationJob.Status.RUNNING
    job.attempts += 1
    job.started_at = timezone.now()
    job.last_error = ""
    job.save(update_fields=["status", "attempts", "started_at", "last_error", "updated_at"])
    report.status = ReportCard.Status.GENERATING
    report.save(update_fields=["status", "updated_at"])
    try:
        content = render_report_card_pdf(report.snapshot)
        checksum = hashlib.sha256(content).hexdigest()
        filename = (
            f"{report.learner.admission_number}-{report.term.academic_year.name}-"
            f"{report.term.name}.pdf"
        ).replace(" ", "-")
        report.pdf.save(filename, ContentFile(content), save=False)
        report.pdf_checksum = checksum
        report.generated_at = timezone.now()
        report.status = ReportCard.Status.READY
        report.save(
            update_fields=[
                "pdf",
                "pdf_checksum",
                "generated_at",
                "status",
                "updated_at",
            ]
        )
        job.status = ReportGenerationJob.Status.COMPLETED
        job.completed_at = timezone.now()
        job.save(update_fields=["status", "completed_at", "updated_at"])
        return checksum
    except Exception as exc:
        report.status = ReportCard.Status.FAILED
        report.save(update_fields=["status", "updated_at"])
        job.status = ReportGenerationJob.Status.FAILED
        job.last_error = str(exc)
        job.save(update_fields=["status", "last_error", "updated_at"])
        raise


@transaction.atomic
def publish_report(*, school, actor, report):
    if not has_school_role(actor, school, "principal", "school_admin"):
        raise PermissionDenied("Principal permission is required.")
    locked = ReportCard.objects.select_for_update().get(pk=report.pk)
    if locked.school_id != school.id:
        raise ValidationError("Report must belong to the same school.")
    if locked.status != ReportCard.Status.READY or not locked.pdf_checksum:
        raise ValidationError("Report PDF must be generated before publication.")
    locked.status = ReportCard.Status.PUBLISHED
    locked.published_by = actor
    locked.published_at = timezone.now()
    locked.save(update_fields=["status", "published_by", "published_at", "updated_at"])
    record_audit_event(
        school=school,
        actor=actor,
        action="reports.report.published",
        target_type="reports.ReportCard",
        target_id=locked.id,
        metadata={"snapshot_hash": locked.snapshot_hash, "pdf_checksum": locked.pdf_checksum},
    )
    return locked
