import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction

from apps.accounts.models import Membership, Role
from apps.tenancy.models import School


@pytest.mark.django_db
def test_email_is_the_user_identifier():
    user = get_user_model().objects.create_user(
        "admin@elora.test",
        password="secret-pass",
    )

    assert user.email == "admin@elora.test"
    assert user.username is None


@pytest.mark.django_db
def test_membership_is_unique_per_user_and_school():
    school = School.objects.create(name="Elora Academy", slug="elora-academy")
    user = get_user_model().objects.create_user("admin@elora.test")
    role = Role.objects.create(code="school_admin", name="School Admin")
    membership = Membership.objects.create(school=school, user=user)
    membership.roles.add(role)

    with pytest.raises(IntegrityError), transaction.atomic():
        Membership.objects.create(school=school, user=user)

    assert list(membership.roles.values_list("code", flat=True)) == ["school_admin"]
