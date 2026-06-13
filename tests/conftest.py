import pytest

from tests.factories import MembershipFactory, SchoolFactory, UserFactory


@pytest.fixture
def school_factory():
    return SchoolFactory


@pytest.fixture
def user_factory():
    return UserFactory


@pytest.fixture
def membership_factory():
    return MembershipFactory
