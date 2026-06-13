from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Count
from django.utils import timezone

from apps.accounts.audit import record_audit_event
from apps.attendance.models import (
    AbsenceAlert,
    AttendanceRegister,
    LearnerAttendanceEntry,
    StaffAttendanceEntry,
)


def _validate_row(*, school, target, target_label, status):
    if target.school_id != school.id:
        raise ValidationError(f"{target_label} must belong to the same school.")
    valid_statuses = {choice for choice, _ in LearnerAttendanceEntry.Status.choices}
    if status not in valid_statuses:
        raise ValidationError(f"{status!r} is not a valid attendance status.")


def _create_alert(*, school, entry):
    values = {"school": school}
    if isinstance(entry, LearnerAttendanceEntry):
        values["learner_entry"] = entry
        guardian = (
            entry.learner.guardian_links.filter(receives_communication=True)
            .select_related("guardian")
            .order_by("-is_primary")
            .first()
        )
        values["recipient_summary"] = (
            guardian.guardian.phone_number if guardian is not None else "No guardian contact"
        )
    else:
        values["staff_entry"] = entry
        values["recipient_summary"] = entry.teacher.phone_number or entry.teacher.employee_number
    return AbsenceAlert.objects.get_or_create(**values)[0]


@transaction.atomic
def mark_learner_attendance(
    *,
    school,
    actor,
    attendance_date,
    session,
    stream,
    rows,
):
    if stream.school_id != school.id:
        raise ValidationError("Stream must belong to the same school.")
    if not rows:
        raise ValidationError("At least one learner attendance row is required.")
    if AttendanceRegister.objects.for_school(school).filter(
        attendance_date=attendance_date,
        session=session,
        subject_type=AttendanceRegister.SubjectType.LEARNER,
        stream=stream,
    ).exists():
        raise ValidationError("A learner attendance register already exists.")

    register = AttendanceRegister(
        school=school,
        attendance_date=attendance_date,
        session=session,
        subject_type=AttendanceRegister.SubjectType.LEARNER,
        stream=stream,
        marked_by=actor,
    )
    register.full_clean()
    register.save()
    seen = set()
    for row in rows:
        learner = row["learner"]
        status = row["status"]
        _validate_row(
            school=school,
            target=learner,
            target_label="Learner",
            status=status,
        )
        if learner.pk in seen:
            raise ValidationError("Each learner may appear only once in a register.")
        seen.add(learner.pk)
        entry = LearnerAttendanceEntry(
            school=school,
            register=register,
            learner=learner,
            status=status,
            arrival_time=row.get("arrival_time"),
            note=row.get("note", ""),
        )
        entry.full_clean()
        entry.save()
        if status == LearnerAttendanceEntry.Status.ABSENT:
            _create_alert(school=school, entry=entry)

    register.status = AttendanceRegister.Status.COMPLETED
    register.completed_at = timezone.now()
    register.save(update_fields=["status", "completed_at", "updated_at"])
    record_audit_event(
        school=school,
        actor=actor,
        action="attendance.learner_register.completed",
        target_type="attendance.AttendanceRegister",
        target_id=register.id,
        metadata={"stream_id": str(stream.id), "entry_count": len(rows)},
    )
    return register


@transaction.atomic
def mark_staff_attendance(*, school, actor, attendance_date, session, rows):
    if not rows:
        raise ValidationError("At least one staff attendance row is required.")
    if AttendanceRegister.objects.for_school(school).filter(
        attendance_date=attendance_date,
        session=session,
        subject_type=AttendanceRegister.SubjectType.STAFF,
    ).exists():
        raise ValidationError("A staff attendance register already exists.")

    register = AttendanceRegister(
        school=school,
        attendance_date=attendance_date,
        session=session,
        subject_type=AttendanceRegister.SubjectType.STAFF,
        marked_by=actor,
    )
    register.full_clean()
    try:
        register.save()
    except IntegrityError as exc:
        raise ValidationError("A staff attendance register already exists.") from exc
    seen = set()
    for row in rows:
        teacher = row["teacher"]
        status = row["status"]
        _validate_row(
            school=school,
            target=teacher,
            target_label="Teacher",
            status=status,
        )
        if teacher.pk in seen:
            raise ValidationError("Each teacher may appear only once in a register.")
        seen.add(teacher.pk)
        entry = StaffAttendanceEntry(
            school=school,
            register=register,
            teacher=teacher,
            status=status,
            arrival_time=row.get("arrival_time"),
            note=row.get("note", ""),
        )
        entry.full_clean()
        entry.save()
        if status == StaffAttendanceEntry.Status.ABSENT:
            _create_alert(school=school, entry=entry)

    register.status = AttendanceRegister.Status.COMPLETED
    register.completed_at = timezone.now()
    register.save(update_fields=["status", "completed_at", "updated_at"])
    record_audit_event(
        school=school,
        actor=actor,
        action="attendance.staff_register.completed",
        target_type="attendance.AttendanceRegister",
        target_id=register.id,
        metadata={"entry_count": len(rows)},
    )
    return register


@transaction.atomic
def correct_attendance(
    *,
    school,
    actor,
    entry,
    new_status,
    reason,
    new_arrival_time=None,
    new_note="",
):
    if entry.school_id != school.id:
        raise ValidationError("Attendance entry must belong to the same school.")
    if not reason.strip():
        raise ValidationError("A correction reason is required.")
    model = type(entry)
    locked = model.objects.select_for_update().get(pk=entry.pk)
    _validate_row(
        school=school,
        target=locked.learner if isinstance(locked, LearnerAttendanceEntry) else locked.teacher,
        target_label="Attendance target",
        status=new_status,
    )
    correction_values = {
        "school": school,
        "old_status": locked.status,
        "new_status": new_status,
        "old_arrival_time": locked.arrival_time,
        "new_arrival_time": new_arrival_time,
        "old_note": locked.note,
        "new_note": new_note,
        "reason": reason,
        "corrected_by": actor,
    }
    if isinstance(locked, LearnerAttendanceEntry):
        correction_values["learner_entry"] = locked
    else:
        correction_values["staff_entry"] = locked

    from apps.attendance.models import AttendanceCorrection

    correction = AttendanceCorrection(**correction_values)
    correction.full_clean()
    correction.save()
    locked.status = new_status
    locked.arrival_time = new_arrival_time
    locked.note = new_note
    locked.full_clean()
    locked.save(update_fields=["status", "arrival_time", "note", "updated_at"])

    alert_filter = (
        {"learner_entry": locked}
        if isinstance(locked, LearnerAttendanceEntry)
        else {"staff_entry": locked}
    )
    if new_status == LearnerAttendanceEntry.Status.ABSENT:
        _create_alert(school=school, entry=locked)
    else:
        AbsenceAlert.objects.for_school(school).filter(**alert_filter).delete()

    record_audit_event(
        school=school,
        actor=actor,
        action="attendance.entry.corrected",
        target_type=f"attendance.{model.__name__}",
        target_id=locked.id,
        metadata={
            "correction_id": str(correction.id),
            "old_status": correction.old_status,
            "new_status": correction.new_status,
            "reason": reason,
        },
    )
    return correction


def attendance_summary(*, school, start_date, end_date, subject_type):
    register_filter = {
        "register__attendance_date__range": (start_date, end_date),
        "register__subject_type": subject_type,
    }
    model = (
        LearnerAttendanceEntry
        if subject_type == AttendanceRegister.SubjectType.LEARNER
        else StaffAttendanceEntry
    )
    counts = {
        item["status"]: item["count"]
        for item in (
            model.objects.for_school(school)
            .filter(**register_filter)
            .values("status")
            .annotate(count=Count("id"))
        )
    }
    total = sum(counts.values())
    present = counts.get(model.Status.PRESENT, 0)
    return {
        "total": total,
        "present": present,
        "absent": counts.get(model.Status.ABSENT, 0),
        "late": counts.get(model.Status.LATE, 0),
        "excused": counts.get(model.Status.EXCUSED, 0),
        "attendance_rate": round((present / total) * 100, 1) if total else 0.0,
    }
