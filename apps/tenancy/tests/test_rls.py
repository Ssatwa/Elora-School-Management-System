from pathlib import Path

import pytest
from django.contrib.auth import get_user_model
from django.db import connection

from apps.accounts.models import Membership
from apps.tenancy.models import School
from apps.tenancy.rls import clear_database_school, set_database_school


def test_rls_migration_forces_membership_policy():
    migration = Path("apps/tenancy/migrations/0002_enable_rls.py").read_text()

    assert "ENABLE ROW LEVEL SECURITY" in migration
    assert "FORCE ROW LEVEL SECURITY" in migration
    assert "app.current_school" in migration


@pytest.mark.django_db(transaction=True)
def test_rls_blocks_cross_school_memberships():
    if connection.vendor != "postgresql":
        pytest.skip("PostgreSQL RLS test")

    first_school = School.objects.create(name="First", slug="first")
    second_school = School.objects.create(name="Second", slug="second")
    first_user = get_user_model().objects.create_user("first@example.test")
    second_user = get_user_model().objects.create_user("second@example.test")

    set_database_school(first_school.id)
    first = Membership.objects.create(school=first_school, user=first_user)
    set_database_school(second_school.id)
    Membership.objects.create(school=second_school, user=second_user)
    set_database_school(first_school.id)

    assert list(Membership.objects.values_list("id", flat=True)) == [first.id]
    clear_database_school()
