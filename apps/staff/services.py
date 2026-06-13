from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q

from apps.accounts.audit import record_audit_event
from apps.staff.models import StaffAssignment


@transaction.atomic
def assign_staff(
    *,
    school,
    actor,
    teacher,
    role,
    start_date,
    department=None,
    learning_area=None,
    grade=None,
    stream=None,
    weekly_lessons=0,
    end_date=None,
):
    duplicate = (
        StaffAssignment.objects.for_school(school)
        .filter(
            teacher=teacher,
            department=department,
            learning_area=learning_area,
            grade=grade,
            stream=stream,
            role=role,
            start_date__lte=end_date or start_date,
        )
        .filter(Q(end_date__isnull=True) | Q(end_date__gte=start_date))
        .exists()
    )
    if duplicate:
        raise ValidationError("Teacher already has an overlapping active assignment.")

    assignment = StaffAssignment(
        school=school,
        teacher=teacher,
        department=department,
        learning_area=learning_area,
        grade=grade,
        stream=stream,
        role=role,
        start_date=start_date,
        end_date=end_date,
        weekly_lessons=weekly_lessons,
    )
    assignment.full_clean()
    assignment.save()
    record_audit_event(
        school=school,
        actor=actor,
        action="staff.assignment.created",
        target_type="staff.StaffAssignment",
        target_id=assignment.id,
        metadata={
            "teacher_id": str(teacher.id),
            "role": role,
            "weekly_lessons": weekly_lessons,
        },
    )
    return assignment
