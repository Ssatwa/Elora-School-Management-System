from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.accounts.audit import record_audit_event
from apps.learners.models import (
    AdmissionApplication,
    AdmissionSequence,
    Enrollment,
    Guardian,
    Learner,
    LearnerGuardian,
    MedicalRecord,
)


def _next_admission_number(*, school, year):
    sequence, _ = AdmissionSequence.objects.select_for_update().get_or_create(
        school=school,
        year=year,
        defaults={"last_number": 0},
    )
    sequence.last_number += 1
    admission_number = f"{year}-{sequence.last_number:04d}"
    while Learner.objects.for_school(school).filter(
        admission_number=admission_number
    ).exists():
        sequence.last_number += 1
        admission_number = f"{year}-{sequence.last_number:04d}"
    sequence.save(update_fields=["last_number", "updated_at"])
    return admission_number


@transaction.atomic
def admit_learner(
    *,
    school,
    actor,
    application,
    academic_year,
    grade,
    stream,
    admission_date,
    learner_data,
    guardians,
    medical_data,
):
    if application.school_id != school.id:
        raise ValidationError("Application must belong to the same school.")
    if application.status != AdmissionApplication.Status.SUBMITTED:
        raise ValidationError("Only submitted applications can be admitted.")

    for label, value in (
        ("Academic year", academic_year),
        ("Grade", grade),
        ("Stream", stream),
    ):
        if value.school_id != school.id:
            raise ValidationError(f"{label} must belong to the same school.")
    if stream.grade_id != grade.id:
        raise ValidationError("Stream must belong to the selected grade.")

    admission_number = _next_admission_number(
        school=school,
        year=admission_date.year,
    )
    learner_values = {
        "first_name": application.first_name,
        "middle_name": application.middle_name,
        "last_name": application.last_name,
        "date_of_birth": application.date_of_birth,
        "gender": application.gender,
        **learner_data,
    }
    learner = Learner(
        school=school,
        admission_number=admission_number,
        admission_date=admission_date,
        **learner_values,
    )
    learner.full_clean()
    learner.save()

    for guardian_values in guardians:
        values = dict(guardian_values)
        relationship = values.pop("relationship")
        is_primary = values.pop("is_primary", False)
        receives_communication = values.pop("receives_communication", True)
        authorized_pickup = values.pop("authorized_pickup", False)
        guardian = Guardian(school=school, **values)
        guardian.full_clean()
        guardian.save()
        link = LearnerGuardian(
            school=school,
            learner=learner,
            guardian=guardian,
            relationship=relationship,
            is_primary=is_primary,
            receives_communication=receives_communication,
            authorized_pickup=authorized_pickup,
        )
        link.full_clean()
        link.save()

    medical_record = MedicalRecord(
        school=school,
        learner=learner,
        **medical_data,
    )
    medical_record.full_clean()
    medical_record.save()

    enrollment = Enrollment(
        school=school,
        learner=learner,
        academic_year=academic_year,
        grade=grade,
        stream=stream,
        start_date=admission_date,
    )
    enrollment.full_clean()
    enrollment.save()

    application.status = AdmissionApplication.Status.ADMITTED
    application.admitted_at = timezone.now()
    application.save(update_fields=["status", "admitted_at", "updated_at"])

    record_audit_event(
        school=school,
        actor=actor,
        action="learners.admission.completed",
        target_type="learners.Learner",
        target_id=learner.id,
        metadata={
            "application_id": str(application.id),
            "admission_number": admission_number,
            "enrollment_id": str(enrollment.id),
        },
    )
    return learner
