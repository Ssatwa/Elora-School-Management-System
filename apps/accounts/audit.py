from apps.accounts.models import AuditLog


def record_audit_event(
    *,
    school,
    actor,
    action,
    target_type,
    target_id,
    request_id="",
    metadata=None,
):
    return AuditLog.objects.create(
        school=school,
        actor=actor,
        action=action,
        target_type=target_type,
        target_id=str(target_id),
        request_id=request_id,
        metadata=metadata or {},
    )
