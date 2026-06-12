import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command

from apps.accounts.models import Membership, Role
from apps.accounts.permissions import has_school_role
from apps.tenancy.models import School


@pytest.mark.django_db
def test_role_check_uses_active_school_membership():
    user = get_user_model().objects.create_user("principal@example.test")
    first = School.objects.create(name="First School", slug="first-school")
    second = School.objects.create(name="Second School", slug="second-school")
    role = Role.objects.create(code="principal", name="Principal")
    membership = Membership.objects.create(user=user, school=first)
    membership.roles.add(role)

    assert has_school_role(user, first, "principal")
    assert not has_school_role(user, second, "principal")


@pytest.mark.django_db
def test_inactive_membership_has_no_roles():
    user = get_user_model().objects.create_user("teacher@example.test")
    school = School.objects.create(name="Elora School", slug="elora-school")
    role = Role.objects.create(code="teacher", name="Teacher")
    membership = Membership.objects.create(user=user, school=school, is_active=False)
    membership.roles.add(role)

    assert not has_school_role(user, school, "teacher")


@pytest.mark.django_db
def test_seed_roles_is_idempotent():
    call_command("seed_roles")
    call_command("seed_roles")

    assert Role.objects.count() == 12
    assert Role.objects.get(code="super_admin").is_platform_role is True
