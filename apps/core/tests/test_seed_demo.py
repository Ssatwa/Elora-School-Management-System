import pytest
from django.core.management import call_command

from apps.accounts.models import Membership, User
from apps.tenancy.models import School


@pytest.mark.django_db
def test_seed_demo_is_idempotent():
    call_command("seed_demo")
    call_command("seed_demo")

    assert School.objects.filter(slug="green-hills").count() == 1
    assert Membership.objects.filter(school__slug="green-hills").count() == 11
    assert (
        User.objects.filter(
            email="super_admin@elora.local",
            is_superuser=True,
        ).count()
        == 1
    )
