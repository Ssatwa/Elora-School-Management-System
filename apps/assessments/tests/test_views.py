import pytest
from django.urls import reverse

from apps.assessments.models import Assessment
from apps.assessments.tests.test_services import setup_assessment
from tests.factories import MembershipFactory

pytestmark = pytest.mark.django_db


def login(client, school, role_code):
    membership = MembershipFactory(school=school, role_code=role_code)
    client.force_login(membership.user)
    return membership


def test_teacher_can_view_only_own_school_assessments(client):
    school, _, _, teacher, own, _, _ = setup_assessment()
    other, _, _, _, other_assessment, _, _ = setup_assessment()
    other.slug = "other-assessment-view"
    other.save(update_fields=["slug"])
    client.force_login(teacher.membership.user)

    response = client.get(
        reverse("assessments:index"),
        HTTP_HOST=f"{school.slug}.localhost",
    )

    content = response.content.decode()
    assert response.status_code == 200
    assert "Assessment operations" in content
    assert own.title in content
    assert str(other_assessment.id) not in content


def test_parent_cannot_view_assessment_operations(client):
    school, *_ = setup_assessment()
    login(client, school, "parent")

    response = client.get(
        reverse("assessments:index"),
        HTTP_HOST=f"{school.slug}.localhost",
    )

    assert response.status_code == 403


def test_department_head_can_moderate_submitted_assessment(client):
    school, _, _, _, assessment, _, _ = setup_assessment()
    membership = login(client, school, "department_head")
    assessment.status = Assessment.Status.SUBMITTED
    assessment.save(update_fields=["status", "updated_at"])

    response = client.post(
        reverse("assessments:moderate", args=[assessment.id]),
        {"comment": "Evidence reviewed."},
        HTTP_HOST=f"{school.slug}.localhost",
    )

    assert response.status_code == 302
    assessment.refresh_from_db()
    assert assessment.status == Assessment.Status.MODERATED
    assert assessment.workflow_events.get().actor == membership.user
