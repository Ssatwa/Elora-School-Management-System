import pytest
from django.urls import reverse

from apps.assessments.tests.test_models import make_learner
from apps.wellbeing.models import DisciplineRecord
from tests.factories import MembershipFactory, SchoolFactory

pytestmark = pytest.mark.django_db


def test_guidance_officer_sees_records_but_parent_is_denied(client):
    school = SchoolFactory()
    learner = make_learner(school)
    officer = MembershipFactory(school=school, role_code="guidance_counsellor")
    DisciplineRecord.objects.create(
        school=school,
        learner=learner,
        category=DisciplineRecord.Category.POSITIVE,
        title="Peer support",
        details="Helped a new learner settle into class.",
        recorded_by=officer.user,
    )
    client.force_login(officer.user)
    response = client.get(
        reverse("wellbeing:index"),
        HTTP_HOST=f"{school.slug}.localhost",
    )
    assert response.status_code == 200
    assert "Peer support" in response.content.decode()

    parent = MembershipFactory(school=school, role_code="parent")
    client.force_login(parent.user)
    denied = client.get(
        reverse("wellbeing:index"),
        HTTP_HOST=f"{school.slug}.localhost",
    )
    assert denied.status_code == 403
