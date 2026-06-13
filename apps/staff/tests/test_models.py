from datetime import date
from typing import cast

import pytest
from django.core.exceptions import ValidationError

from apps.academics.models import Grade, LearningArea, Stream
from apps.accounts.models import Membership
from apps.staff.models import Department, StaffAssignment, TeacherProfile
from apps.tenancy.models import School
from tests.factories import MembershipFactory, SchoolFactory

pytestmark = pytest.mark.django_db


def create_teacher(school: School, employee_number: str = "EMP-001") -> TeacherProfile:
    membership = cast(
        Membership,
        MembershipFactory(school=school, role_code="teacher"),
    )
    return TeacherProfile.objects.create(
        school=school,
        membership=membership,
        employee_number=employee_number,
        employment_date=date(2024, 1, 8),
    )


def test_teacher_profile_requires_membership_from_same_school():
    first_school = cast(School, SchoolFactory())
    second_school = cast(School, SchoolFactory())
    membership = cast(
        Membership,
        MembershipFactory(school=first_school, role_code="teacher"),
    )
    profile = TeacherProfile(
        school=second_school,
        membership=membership,
        employee_number="EMP-001",
        employment_date=date(2024, 1, 8),
    )

    with pytest.raises(ValidationError, match="same school"):
        profile.full_clean()


def test_department_head_must_belong_to_department_school():
    first_school = cast(School, SchoolFactory())
    second_school = cast(School, SchoolFactory())
    teacher = create_teacher(first_school)
    department = Department(
        school=second_school,
        code="SCI",
        name="Sciences",
        head=teacher,
    )

    with pytest.raises(ValidationError, match="same school"):
        department.full_clean()


def test_staff_assignment_requires_same_school_references():
    first_school = cast(School, SchoolFactory())
    second_school = cast(School, SchoolFactory())
    teacher = create_teacher(first_school)
    learning_area = LearningArea.objects.create(
        school=second_school,
        code="MATH",
        name="Mathematics",
    )
    assignment = StaffAssignment(
        school=first_school,
        teacher=teacher,
        learning_area=learning_area,
        role=StaffAssignment.Role.SUBJECT_TEACHER,
        start_date=date(2026, 1, 1),
        weekly_lessons=5,
    )

    with pytest.raises(ValidationError, match="same school"):
        assignment.full_clean()


def test_teacher_workload_sums_current_assignments():
    school = cast(School, SchoolFactory())
    teacher = create_teacher(school)
    grade = Grade.objects.create(
        school=school,
        code="G7",
        name="Grade 7",
        education_level=Grade.EducationLevel.JUNIOR_SCHOOL,
        order=7,
    )
    stream = Stream.objects.create(
        school=school,
        grade=grade,
        code="E",
        name="East",
    )
    mathematics = LearningArea.objects.create(
        school=school,
        code="MATH",
        name="Mathematics",
    )
    science = LearningArea.objects.create(
        school=school,
        code="SCI",
        name="Integrated Science",
    )
    for learning_area, lessons in ((mathematics, 5), (science, 4)):
        StaffAssignment.objects.create(
            school=school,
            teacher=teacher,
            learning_area=learning_area,
            grade=grade,
            stream=stream,
            role=StaffAssignment.Role.SUBJECT_TEACHER,
            start_date=date(2026, 1, 1),
            weekly_lessons=lessons,
        )

    assert teacher.current_weekly_lessons == 9


def test_staff_assignment_end_date_cannot_precede_start_date():
    school = cast(School, SchoolFactory())
    assignment = StaffAssignment(
        school=school,
        teacher=create_teacher(school),
        role=StaffAssignment.Role.CLASS_TEACHER,
        start_date=date(2026, 5, 1),
        end_date=date(2026, 4, 1),
    )

    with pytest.raises(ValidationError, match="end date"):
        assignment.full_clean()
