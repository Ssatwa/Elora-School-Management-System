import pytest
from django.urls import reverse

from apps.finance.tests.test_services import setup_finance
from apps.learners.models import Guardian, LearnerGuardian
from tests.factories import MembershipFactory

pytestmark = pytest.mark.django_db


def test_accountant_can_view_finance_dashboard(client):
    school, _, _, accountant = setup_finance()
    client.force_login(accountant.user)

    response = client.get(
        reverse("finance:index"),
        HTTP_HOST=f"{school.slug}.localhost",
    )

    assert response.status_code == 200
    assert "Finance operations" in response.content.decode()


def test_parent_statement_is_limited_to_linked_learner(client):
    school, _, learner, _ = setup_finance()
    parent = MembershipFactory(school=school, role_code="parent")
    guardian = Guardian.objects.create(
        school=school,
        membership=parent,
        first_name="Wanjiku",
        last_name="Kamau",
        email="parent@example.test",
        phone_number="+254700000001",
    )
    LearnerGuardian.objects.create(
        school=school,
        learner=learner,
        guardian=guardian,
        relationship=LearnerGuardian.Relationship.MOTHER,
        is_primary=True,
    )
    client.force_login(parent.user)

    response = client.get(
        reverse("finance:index"),
        HTTP_HOST=f"{school.slug}.localhost",
    )

    assert response.status_code == 200
    assert learner.full_name in response.content.decode()


def test_parent_cannot_open_unlinked_learner_statement(client):
    school, _, learner, _ = setup_finance()
    parent = MembershipFactory(school=school, role_code="parent")
    client.force_login(parent.user)

    response = client.get(
        reverse("finance:statement", args=[learner.id]),
        HTTP_HOST=f"{school.slug}.localhost",
    )

    assert response.status_code == 404
