from django.contrib import admin

from apps.accounts.models import AuditLog, Membership, Role, User
from apps.tenancy.models import School, SchoolDomain


def test_foundation_models_are_registered_in_admin():
    for model in (School, SchoolDomain, User, Role, Membership, AuditLog):
        assert model in admin.site._registry


def test_audit_admin_is_read_only():
    audit_admin = admin.site._registry[AuditLog]

    assert audit_admin.has_add_permission(None) is False
    assert audit_admin.has_change_permission(None) is False
    assert audit_admin.has_delete_permission(None) is False
