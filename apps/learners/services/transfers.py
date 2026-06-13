from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.accounts.audit import record_audit_event
from apps.learners.models import Enrollment, Learner, TransferRecord


@transaction.atomic
def transfer_learner(
    *,
    school,
    actor,
    learner,
    destination_school_name,
    transfer_date,
    reason,
    export_reference="",
):
    if learner.school_id != school.id:
        raise ValidationError("Learner must belong to the same school.")

    locked_learner = Learner.objects.select_for_update().get(pk=learner.pk)
    enrollment = (
        Enrollment.objects.select_for_update()
        .for_school(school)
        .filter(
            learner=locked_learner,
            status=Enrollment.Status.ACTIVE,
        )
        .first()
    )
    if enrollment is None:
        raise ValidationError("Learner has no active enrollment to transfer.")

    now = timezone.now()
    transfer = TransferRecord(
        school=school,
        learner=locked_learner,
        enrollment=enrollment,
        destination_school_name=destination_school_name,
        transfer_date=transfer_date,
        reason=reason,
        status=TransferRecord.Status.COMPLETED,
        export_reference=export_reference,
        exported_at=now if export_reference else None,
        completed_at=now,
    )
    transfer.full_clean()
    transfer.save()

    enrollment.status = Enrollment.Status.TRANSFERRED
    enrollment.end_date = transfer_date
    enrollment.full_clean()
    enrollment.save(update_fields=["status", "end_date", "updated_at"])

    locked_learner.status = Learner.Status.TRANSFERRED
    locked_learner.save(update_fields=["status", "updated_at"])

    record_audit_event(
        school=school,
        actor=actor,
        action="learners.transfer.completed",
        target_type="learners.TransferRecord",
        target_id=transfer.id,
        metadata={
            "learner_id": str(locked_learner.id),
            "enrollment_id": str(enrollment.id),
            "destination_school_name": destination_school_name,
            "export_reference": export_reference,
        },
    )
    return transfer
