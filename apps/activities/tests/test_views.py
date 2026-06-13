import pytest
from django.urls import reverse

from apps.activities.models import ActivityParticipation, Club
from apps.assessments.tests.test_models import make_learner
from tests.factories import MembershipFactory, SchoolFactory

pytestmark = pytest.mark.django_db


def test_teacher_can_view_club_participation(client):
    school = SchoolFactory()
    teacher = MembershipFactory(school=school, role_code="teacher")
    learner = make_learner(school)
    club = Club.objects.create(
        school=school,
        name="Robotics Club",
        category="STEM",
        patron=teacher,
    )
    ActivityParticipation.objects.create(
        school=school,
        club=club,
        learner=learner,
        role="Member",
        is_active=True,
    )
    client.force_login(teacher.user)
    response = client.get(
        reverse("activities:index"),
        HTTP_HOST=f"{school.slug}.localhost",
    )
    assert response.status_code == 200
    assert "Robotics Club" in response.content.decode()
