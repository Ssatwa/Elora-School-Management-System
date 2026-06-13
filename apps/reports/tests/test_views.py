import pytest
from django.urls import reverse

from apps.learners.models import Guardian, LearnerGuardian
from apps.reports.services import create_report_snapshot, generate_report_pdf, publish_report
from apps.reports.tests.test_reports import setup_approved_result
from tests.factories import MembershipFactory

pytestmark = pytest.mark.django_db


def login(client, school, role_code):
    membership = MembershipFactory(school=school, role_code=role_code)
    client.force_login(membership.user)
    return membership


def build_published_report():
    school, term, learner = setup_approved_result()
    principal = MembershipFactory(school=school, role_code="principal")
    report = create_report_snapshot(
        school=school,
        actor=principal.user,
        learner=learner,
        term=term,
        principal_remark="Consistent progress.",
    )
    generate_report_pdf(report_id=report.id, school_id=school.id)
    report.refresh_from_db()
    publish_report(school=school, actor=principal.user, report=report)
    report.refresh_from_db()
    return school, report


def test_principal_can_view_report_dashboard_without_cross_school_leak(client):
    school, own = build_published_report()
    other, other_report = build_published_report()
    other.slug = "other-report-view"
    other.save(update_fields=["slug"])
    login(client, school, "principal")

    response = client.get(
        reverse("reports:index"),
        HTTP_HOST=f"{school.slug}.localhost",
    )

    content = response.content.decode()
    assert response.status_code == 200
    assert "CBC report cards" in content
    assert own.learner.full_name in content
    assert str(other_report.id) not in content


def test_authorized_school_leader_can_download_published_pdf(client):
    school, report = build_published_report()
    login(client, school, "principal")

    response = client.get(
        reverse("reports:download", args=[report.id]),
        HTTP_HOST=f"{school.slug}.localhost",
    )

    assert response.status_code == 200
    assert response["Content-Type"] == "application/pdf"
    assert b"".join(response.streaming_content).startswith(b"%PDF")


def test_report_download_does_not_allow_other_school(client):
    school, _ = build_published_report()
    other, report = build_published_report()
    other.slug = "other-report-download"
    other.save(update_fields=["slug"])
    login(client, school, "principal")

    response = client.get(
        reverse("reports:download", args=[report.id]),
        HTTP_HOST=f"{school.slug}.localhost",
    )

    assert response.status_code == 404


def test_parent_can_only_download_linked_learners_published_report(client):
    school, report = build_published_report()
    parent = login(client, school, "parent")
    guardian = Guardian.objects.create(
        school=school,
        membership=parent,
        first_name="Wanjiku",
        last_name="Kamau",
        email=parent.user.email,
        phone_number="+254700000009",
    )
    LearnerGuardian.objects.create(
        school=school,
        learner=report.learner,
        guardian=guardian,
        relationship=LearnerGuardian.Relationship.MOTHER,
        is_primary=True,
    )

    dashboard = client.get(
        reverse("reports:index"),
        HTTP_HOST=f"{school.slug}.localhost",
    )
    download = client.get(
        reverse("reports:download", args=[report.id]),
        HTTP_HOST=f"{school.slug}.localhost",
    )

    assert dashboard.status_code == 200
    assert report.learner.full_name in dashboard.content.decode()
    assert download.status_code == 200


def test_parent_cannot_download_unlinked_learners_report(client):
    school, report = build_published_report()
    login(client, school, "parent")

    response = client.get(
        reverse("reports:download", args=[report.id]),
        HTTP_HOST=f"{school.slug}.localhost",
    )

    assert response.status_code == 404
