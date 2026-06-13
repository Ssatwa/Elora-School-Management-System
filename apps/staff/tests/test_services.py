from datetime import date
from typing import cast

import pytest
from django.core.exceptions import ValidationError

from apps.academics.models import LearningArea
from apps.accounts.models import AuditLog, Membership, User
from apps.staff.models import StaffAssignment, TeacherProfile
from apps.staff.services import assign_staff
from apps.tenancy.models import School
from tests.factories import MembershipFactory, SchoolFactory, UserFactory

pytestmark = pytest.mark.django_db


def create_teacher(school: School) -> TeacherProfile:
    membership = cast(
        Membership,
        MembershipFactory(school=school, role_code="teacher"),
    )
    return TeacherProfile.objects.create(
        school=school,
        membership=membership,
        employee_number="EMP-001",
        employment_date=date(2024, 1, 8),
    )


def test_assign_staff_records_audit_event():
    school = cast(School, SchoolFactory())
    actor = cast(User, UserFactory())
    teacher = create_teacher(school)
    learning_area = LearningArea.objects.create(
        school=school,
        code="MATH",
        name="Mathematics",
    )

    assignment = assign_staff(
        school=school,
        actor=actor,
        teacher=teacher,
        role=StaffAssignment.Role.SUBJECT_TEACHER,
        start_date=date(2026, 1, 1),
        learning_area=learning_area,
        weekly_lessons=5,
    )

    event = AuditLog.objects.get(target_id=str(assignment.id))
    assert event.school == school
    assert event.actor == actor
    assert event.action == "staff.assignment.created"


def test_assign_staff_rejects_duplicate_active_assignment():
    school = cast(School, SchoolFactory())
    actor = cast(User, UserFactory())
    teacher = create_teacher(school)
    learning_area = LearningArea.objects.create(
        school=school,
        code="MATH",
        name="Mathematics",
    )
    values = {
        "school": school,
        "actor": actor,
        "teacher": teacher,
        "role": StaffAssignment.Role.SUBJECT_TEACHER,
        "start_date": date(2026, 1, 1),
        "learning_area": learning_area,
        "weekly_lessons": 5,
    }
    assign_staff(**values)

    with pytest.raises(ValidationError, match="active assignment"):
        assign_staff(**values)

    assert StaffAssignment.objects.count() == 1
    assert AuditLog.objects.filter(action="staff.assignment.created").count() == 1


def test_assign_staff_rolls_back_cross_school_assignment():
    first_school = cast(School, SchoolFactory())
    second_school = cast(School, SchoolFactory())
    actor = cast(User, UserFactory())
    learning_area = LearningArea.objects.create(
        school=second_school,
        code="MATH",
        name="Mathematics",
    )

    with pytest.raises(ValidationError, match="same school"):
        assign_staff(
            school=first_school,
            actor=actor,
            teacher=create_teacher(first_school),
            role=StaffAssignment.Role.SUBJECT_TEACHER,
            start_date=date(2026, 1, 1),
            learning_area=learning_area,
        )

    assert StaffAssignment.objects.count() == 0
    assert AuditLog.objects.filter(action="staff.assignment.created").count() == 0
