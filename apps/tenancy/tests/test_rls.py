from pathlib import Path

import pytest
from django.contrib.auth import get_user_model
from django.db import connection

from apps.accounts.models import Membership
from apps.learners.models import Learner
from apps.tenancy.models import School
from apps.tenancy.rls import clear_database_school, set_database_school


def test_rls_migration_forces_membership_policy():
    migration = Path("apps/tenancy/migrations/0002_enable_rls.py").read_text()

    assert "ENABLE ROW LEVEL SECURITY" in migration
    assert "FORCE ROW LEVEL SECURITY" in migration
    assert "app.current_school" in migration


def test_milestone_two_rls_migration_covers_every_tenant_table():
    migration = Path("apps/tenancy/migrations/0003_milestone_2_rls.py").read_text()
    expected_tables = {
        "academics_academicyear",
        "academics_term",
        "academics_grade",
        "academics_stream",
        "academics_learningarea",
        "academics_strand",
        "academics_substrand",
        "academics_learningoutcome",
        "academics_competency",
        "academics_outcomecompetency",
        "staff_teacherprofile",
        "staff_department",
        "staff_staffassignment",
        "learners_learner",
        "learners_guardian",
        "learners_learnerguardian",
        "learners_medicalrecord",
        "learners_admissionapplication",
        "learners_admissionsequence",
        "learners_enrollment",
        "learners_transferrecord",
    }

    for table in expected_tables:
        assert table in migration
    assert "FORCE ROW LEVEL SECURITY" in migration


def test_milestone_three_rls_migration_covers_every_tenant_table():
    migration = Path("apps/tenancy/migrations/0004_milestone_3_rls.py").read_text()
    expected_tables = {
        "attendance_attendanceregister",
        "attendance_learnerattendanceentry",
        "attendance_staffattendanceentry",
        "attendance_attendancecorrection",
        "attendance_absencealert",
        "timetabling_room",
        "timetabling_timetableperiod",
        "timetabling_timetable",
        "timetabling_timetableentry",
    }

    for table in expected_tables:
        assert table in migration
    assert "FORCE ROW LEVEL SECURITY" in migration


def test_milestone_four_rls_migration_covers_every_tenant_table():
    migration = Path("apps/tenancy/migrations/0005_milestone_4_rls.py").read_text()
    expected_tables = {
        "assessments_ratinglevel",
        "assessments_rubric",
        "assessments_rubriccriterion",
        "assessments_assessment",
        "assessments_assessmentresult",
        "assessments_criterionrating",
        "assessments_evidence",
        "assessments_assessmentworkflowevent",
        "reports_reportcard",
        "reports_reportgenerationjob",
    }

    for table in expected_tables:
        assert table in migration
    assert "FORCE ROW LEVEL SECURITY" in migration


def test_milestone_five_rls_migration_covers_every_finance_table():
    migration = Path("apps/tenancy/migrations/0006_milestone_5_rls.py").read_text()
    for table in {
        "finance_feestructure",
        "finance_invoice",
        "finance_payment",
        "finance_paymentallocation",
        "finance_receipt",
    }:
        assert table in migration
    assert "FORCE ROW LEVEL SECURITY" in migration


@pytest.mark.django_db(transaction=True)
def test_rls_blocks_cross_school_memberships():
    if connection.vendor != "postgresql":
        pytest.skip("PostgreSQL RLS test")

    first_school = School.objects.create(name="First", slug="first")
    second_school = School.objects.create(name="Second", slug="second")
    first_user = get_user_model().objects.create_user("first@example.test")
    second_user = get_user_model().objects.create_user("second@example.test")

    set_database_school(first_school.id)
    first = Membership.objects.create(school=first_school, user=first_user)
    set_database_school(second_school.id)
    Membership.objects.create(school=second_school, user=second_user)
    set_database_school(first_school.id)

    assert list(Membership.objects.values_list("id", flat=True)) == [first.id]
    clear_database_school()


@pytest.mark.django_db(transaction=True)
def test_rls_blocks_cross_school_learners():
    if connection.vendor != "postgresql":
        pytest.skip("PostgreSQL RLS test")

    first_school = School.objects.create(name="First", slug="first-learners")
    second_school = School.objects.create(name="Second", slug="second-learners")
    learner_values = {
        "first_name": "Amina",
        "last_name": "Kamau",
        "date_of_birth": "2013-06-12",
        "gender": Learner.Gender.FEMALE,
        "admission_date": "2026-01-06",
    }

    set_database_school(first_school.id)
    first = Learner.objects.create(
        school=first_school,
        admission_number="2026-0001",
        **learner_values,
    )
    set_database_school(second_school.id)
    Learner.objects.create(
        school=second_school,
        admission_number="2026-0001",
        **learner_values,
    )
    set_database_school(first_school.id)

    assert list(Learner.objects.values_list("id", flat=True)) == [first.id]
    clear_database_school()
