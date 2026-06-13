from datetime import date

import pytest
from django.urls import reverse

from apps.assessments.tests.test_models import make_context, make_learner
from apps.learners.models import Enrollment
from apps.learning.services import publish_assignment, submit_assignment
from tests.factories import MembershipFactory, SchoolFactory

pytestmark = pytest.mark.django_db


def test_teacher_publishes_assignment_and_learner_submits(client):
    school = SchoolFactory()
    year, term, _, stream, area, teacher = make_context(school)
    learner = make_learner(school)
    learner.membership = MembershipFactory(school=school, role_code="learner")
    learner.save(update_fields=["membership"])
    Enrollment.objects.create(
        school=school,
        learner=learner,
        academic_year=year,
        grade=stream.grade,
        stream=stream,
        start_date=date(2026, 1, 6),
    )
    assignment = publish_assignment(
        school=school,
        actor=teacher.membership.user,
        teacher=teacher,
        term=term,
        stream=stream,
        learning_area=area,
        title="Numbers practice",
        instructions="Complete questions 1 to 10.",
        due_at="2026-06-20T17:00:00+03:00",
    )
    submission = submit_assignment(
        school=school,
        actor=learner.membership.user,
        assignment=assignment,
        learner=learner,
        response="My completed number patterns.",
    )

    assert assignment.is_published
    assert submission.response.startswith("My completed")

    client.force_login(teacher.membership.user)
    response = client.get(
        reverse("learning:index"),
        HTTP_HOST=f"{school.slug}.localhost",
    )
    assert response.status_code == 200
    assert assignment.title in response.content.decode()
