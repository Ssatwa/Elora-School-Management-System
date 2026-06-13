from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.utils import timezone

from apps.accounts.audit import record_audit_event
from apps.accounts.permissions import has_school_role
from apps.learners.models import Enrollment, MedicalRecord
from apps.staff.models import StaffAssignment

MEDICAL_OVERSIGHT_ROLES = (
    "school_admin",
    "principal",
    "deputy_principal",
    "guidance_counsellor",
)


def can_view_medical_record(user, school, learner):
    if not user.is_authenticated or school is None or learner.school_id != school.id:
        return False
    if has_school_role(user, school, *MEDICAL_OVERSIGHT_ROLES):
        return True
    if not has_school_role(user, school, "class_teacher"):
        return False

    enrollment = (
        Enrollment.objects.for_school(school)
        .filter(learner=learner, status=Enrollment.Status.ACTIVE)
        .only("stream_id")
        .first()
    )
    if enrollment is None:
        return False

    today = timezone.localdate()
    return (
        StaffAssignment.objects.for_school(school)
        .filter(
            teacher__membership__user=user,
            role=StaffAssignment.Role.CLASS_TEACHER,
            stream_id=enrollment.stream_id,
            start_date__lte=today,
        )
        .filter(Q(end_date__isnull=True) | Q(end_date__gte=today))
        .exists()
    )


def access_medical_record(user, school, learner):
    if not can_view_medical_record(user, school, learner):
        raise PermissionDenied
    record = MedicalRecord.objects.for_school(school).get(learner=learner)
    record_audit_event(
        school=school,
        actor=user,
        action="learners.medical.accessed",
        target_type="learners.MedicalRecord",
        target_id=record.id,
        metadata={"learner_id": str(learner.id)},
    )
    return record
