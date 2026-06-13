import pytest
from django.contrib.auth import get_user_model

from apps.accounts.audit import record_audit_event
from apps.accounts.models import AuditLog
from apps.tenancy.models import School


@pytest.mark.django_db
def test_audit_event_keeps_school_actor_and_request_id():
    school = School.objects.create(name="Green Hills", slug="green-hills")
    actor = get_user_model().objects.create_user("admin@example.test")

    event = record_audit_event(
        school=school,
        actor=actor,
        action="membership.created",
        target_type="Membership",
        target_id="abc",
        request_id="request-123",
        metadata={"role": "teacher"},
    )

    stored = AuditLog.objects.get(pk=event.pk)
    assert stored.school == school
    assert stored.actor == actor
    assert stored.request_id == "request-123"
    assert stored.metadata == {"role": "teacher"}
