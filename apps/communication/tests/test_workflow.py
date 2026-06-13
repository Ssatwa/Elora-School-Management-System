import pytest
from django.urls import reverse

from apps.communication.models import Notification
from apps.communication.services import publish_announcement
from tests.factories import MembershipFactory, SchoolFactory

pytestmark = pytest.mark.django_db


def test_teacher_announcement_notifies_parent_and_is_visible(client):
    school = SchoolFactory()
    teacher = MembershipFactory(school=school, role_code="teacher")
    parent = MembershipFactory(school=school, role_code="parent")

    announcement = publish_announcement(
        school=school,
        actor=teacher.user,
        title="Family learning afternoon",
        body="Join us on Friday at 2 PM.",
        recipients=[parent.user],
    )

    assert Notification.objects.for_school(school).filter(
        user=parent.user,
        announcement=announcement,
    ).exists()
    client.force_login(parent.user)
    response = client.get(
        reverse("communication:index"),
        HTTP_HOST=f"{school.slug}.localhost",
    )
    assert response.status_code == 200
    assert announcement.title in response.content.decode()
