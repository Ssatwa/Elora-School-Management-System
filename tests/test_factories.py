import pytest

from tests.factories import MembershipFactory


@pytest.mark.django_db
def test_membership_factory_creates_primary_school_domain():
    membership = MembershipFactory(role_code="teacher")

    assert membership.school.domains.get(is_primary=True).hostname.endswith(
        ".localhost"
    )
    assert membership.roles.get().code == "teacher"
