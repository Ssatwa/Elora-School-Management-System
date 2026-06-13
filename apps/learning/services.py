from django.core.exceptions import PermissionDenied, ValidationError
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from apps.accounts.permissions import has_school_role
from apps.learners.models import Enrollment
from apps.learning.models import Assignment, Submission


def publish_assignment(
    *,
    school,
    actor,
    teacher,
    term,
    stream,
    learning_area,
    title,
    instructions,
    due_at,
):
    if teacher.membership.user_id != actor.id or not has_school_role(
        actor, school, "teacher", "class_teacher", "department_head"
    ):
        raise PermissionDenied("Only the assigned teacher can publish this assignment.")
    parsed_due_at = parse_datetime(due_at) if isinstance(due_at, str) else due_at
    if parsed_due_at is None:
        raise ValidationError("A valid due date is required.")
    return Assignment.objects.create(
        school=school,
        teacher=teacher,
        term=term,
        stream=stream,
        learning_area=learning_area,
        title=title,
        instructions=instructions,
        due_at=parsed_due_at,
        is_published=True,
        published_at=timezone.now(),
    )


def submit_assignment(*, school, actor, assignment, learner, response):
    if learner.membership is None or learner.membership.user_id != actor.id:
        raise PermissionDenied("Learners may only submit their own work.")
    if assignment.school_id != school.id or learner.school_id != school.id:
        raise ValidationError("Assignment and learner must belong to the same school.")
    if not Enrollment.objects.for_school(school).filter(
        learner=learner,
        stream=assignment.stream,
        status=Enrollment.Status.ACTIVE,
    ).exists():
        raise ValidationError("Learner is not enrolled in this class.")
    submission, _ = Submission.objects.update_or_create(
        school=school,
        assignment=assignment,
        learner=learner,
        defaults={"response": response},
    )
    return submission
