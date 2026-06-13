from collections import defaultdict

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.accounts.audit import record_audit_event
from apps.timetabling.models import Timetable, TimetableEntry


def _require_same_school(school, **values):
    for label, value in values.items():
        if value.school_id != school.id:
            raise ValidationError(
                f"{label.replace('_', ' ').title()} must belong to the same school."
            )


@transaction.atomic
def add_timetable_entry(
    *,
    school,
    actor,
    timetable,
    period,
    stream,
    learning_area,
    teacher,
    room,
):
    _require_same_school(
        school,
        timetable=timetable,
        period=period,
        stream=stream,
        learning_area=learning_area,
        teacher=teacher,
        room=room,
    )
    locked_timetable = Timetable.objects.select_for_update().get(pk=timetable.pk)
    if locked_timetable.status != Timetable.Status.DRAFT:
        raise ValidationError("Draft timetables are the only timetables that can be edited.")
    same_period = TimetableEntry.objects.for_school(school).filter(
        timetable=locked_timetable,
        period=period,
    )
    if same_period.filter(stream=stream, learning_area=learning_area).exists():
        raise ValidationError(
            "Learning area conflict: this stream already has that learning area in this period."
        )
    conflicts = (
        ("teacher", teacher, "Teacher conflict"),
        ("room", room, "Room conflict"),
        ("stream", stream, "Stream conflict"),
    )
    for field_name, value, message in conflicts:
        if same_period.filter(**{field_name: value}).exists():
            raise ValidationError(f"{message}: already assigned in this period.")
    entry = TimetableEntry(
        school=school,
        timetable=locked_timetable,
        period=period,
        stream=stream,
        learning_area=learning_area,
        teacher=teacher,
        room=room,
    )
    entry.full_clean()
    entry.save()
    record_audit_event(
        school=school,
        actor=actor,
        action="timetabling.entry.created",
        target_type="timetabling.TimetableEntry",
        target_id=entry.id,
        metadata={"timetable_id": str(timetable.id), "period_id": str(period.id)},
    )
    return entry


def validate_timetable(*, school, timetable):
    if timetable.school_id != school.id:
        raise ValidationError("Timetable must belong to the same school.")
    entries = list(
        TimetableEntry.objects.for_school(school)
        .filter(timetable=timetable)
        .select_related("period", "teacher", "room", "stream", "learning_area")
    )
    errors = []
    dimensions = {
        "teacher": "Teacher",
        "room": "Room",
        "stream": "Stream",
    }
    for field_name, label in dimensions.items():
        grouped = defaultdict(list)
        for entry in entries:
            grouped[(entry.period_id, getattr(entry, f"{field_name}_id"))].append(entry)
        for duplicate_entries in grouped.values():
            if len(duplicate_entries) > 1:
                first = duplicate_entries[0]
                errors.append(
                    f"{label} conflict in {first.period}: "
                    f"{getattr(first, field_name)} is assigned more than once."
                )
    grouped_areas = defaultdict(list)
    for entry in entries:
        grouped_areas[(entry.period_id, entry.stream_id, entry.learning_area_id)].append(entry)
    for duplicate_entries in grouped_areas.values():
        if len(duplicate_entries) > 1:
            first = duplicate_entries[0]
            errors.append(
                f"Learning area conflict in {first.period}: "
                f"{first.stream} has {first.learning_area} more than once."
            )
    return errors


@transaction.atomic
def publish_timetable(*, school, actor, timetable):
    if timetable.school_id != school.id:
        raise ValidationError("Timetable must belong to the same school.")
    locked = Timetable.objects.select_for_update().get(pk=timetable.pk)
    if locked.status != Timetable.Status.DRAFT:
        raise ValidationError("Only draft timetables can be published.")
    if not locked.entries.exists():
        raise ValidationError("A timetable requires at least one entry before publication.")
    conflicts = validate_timetable(school=school, timetable=locked)
    if conflicts:
        raise ValidationError(conflicts)

    locked.status = Timetable.Status.PUBLISHED
    locked.published_by = actor
    locked.published_at = timezone.now()
    locked.save(update_fields=["status", "published_by", "published_at", "updated_at"])
    record_audit_event(
        school=school,
        actor=actor,
        action="timetabling.timetable.published",
        target_type="timetabling.Timetable",
        target_id=locked.id,
        metadata={"entry_count": locked.entries.count()},
    )
    return locked
