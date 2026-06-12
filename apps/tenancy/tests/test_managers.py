import pytest
from django.contrib.auth import get_user_model

from apps.accounts.models import Membership
from apps.tenancy.models import School


@pytest.mark.django_db
def test_tenant_queryset_requires_explicit_school():
    first = School.objects.create(name="First School", slug="first")
    second = School.objects.create(name="Second School", slug="second")
    user_model = get_user_model()
    first_user = user_model.objects.create_user("first@example.test")
    second_user = user_model.objects.create_user("second@example.test")
    Membership.objects.create(school=first, user=first_user)
    Membership.objects.create(school=second, user=second_user)

    memberships = Membership.objects.for_school(first)

    assert list(memberships.values_list("user__email", flat=True)) == [
        "first@example.test"
    ]


@pytest.mark.django_db
def test_tenant_queryset_rejects_missing_school():
    with pytest.raises(ValueError, match="school is required"):
        Membership.objects.for_school(None)
