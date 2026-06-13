from django.core.exceptions import PermissionDenied
from django.utils import timezone

from apps.accounts.permissions import has_school_role
from apps.communication.models import Announcement, Notification


def publish_announcement(*, school, actor, title, body, recipients):
    if not has_school_role(
        actor,
        school,
        "school_admin",
        "principal",
        "deputy_principal",
        "teacher",
        "class_teacher",
        "department_head",
    ):
        raise PermissionDenied("Announcement publishing permission is required.")
    announcement = Announcement.objects.create(
        school=school,
        title=title,
        body=body,
        published_by=actor,
        published_at=timezone.now(),
    )
    Notification.objects.bulk_create(
        [
            Notification(
                school=school,
                user=user,
                announcement=announcement,
                title=title,
                body=body,
            )
            for user in recipients
        ]
    )
    return announcement
