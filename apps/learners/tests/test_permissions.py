from datetime import date
from typing import cast

import pytest
from django.core.exceptions import PermissionDenied

from apps.academics.models import AcademicYear, Grade, Stream
from apps.accounts.models import AuditLog, Membership
from apps.learners.models import Enrollment, Learner, MedicalRecord
from apps.learners.permissions import access_medical_record, can_view_medical_record
from apps.staff.models import StaffAssignment, TeacherProfile
from apps.tenancy.models import School
from tests.factories import MembershipFactory, SchoolFactory

pytestmark = pytest.mark.django_db


def create_medical_context(school: School):
    learner = Learner.objects.create(
        school=school,
        admission_number="2026-0001",
        first_name="Amina",
        last_name="Kamau",
        date_of_birth=date(2013, 6, 12),
        gender=Learner.Gender.FEMALE,
        admission_date=date(2026, 1, 6),
    )
    academic_year = AcademicYear.objects.create(
        school=school,
        name="2026",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
        status=AcademicYear.Status.ACTIVE,
    )
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
    Enrollment.objects.create(
        school=school,
        learner=learner,
        academic_year=academic_year,
        grade=grade,
        stream=stream,
        start_date=date(2026, 1, 6),
    )
    record = MedicalRecord.objects.create(
        school=school,
        learner=learner,
        allergies="Peanuts",
    )
    return learner, stream, record


@pytest.mark.parametrize(
    "role_code",
    ["school_admin", "principal", "deputy_principal", "guidance_counsellor"],
)
def test_authorized_roles_can_access_medical_record(role_code):
    school = cast(School, SchoolFactory())
    learner, _, record = create_medical_context(school)
    membership = cast(
        Membership,
        MembershipFactory(school=school, role_code=role_code),
    )

    assert can_view_medical_record(membership.user, school, learner)
    assert access_medical_record(membership.user, school, learner) == record
    assert AuditLog.objects.filter(
        action="learners.medical.accessed",
        actor=membership.user,
        target_id=str(record.id),
    ).exists()


def test_assigned_class_teacher_can_access_medical_record():
    school = cast(School, SchoolFactory())
    learner, stream, record = create_medical_context(school)
    membership = cast(
        Membership,
        MembershipFactory(school=school, role_code="class_teacher"),
    )
    teacher = TeacherProfile.objects.create(
        school=school,
        membership=membership,
        employee_number="EMP-001",
        employment_date=date(2024, 1, 8),
    )
    StaffAssignment.objects.create(
        school=school,
        teacher=teacher,
        grade=stream.grade,
        stream=stream,
        role=StaffAssignment.Role.CLASS_TEACHER,
        start_date=date(2026, 1, 1),
    )

    assert access_medical_record(membership.user, school, learner) == record


@pytest.mark.parametrize("role_code", ["teacher", "parent"])
def test_unassigned_roles_cannot_access_medical_record(role_code):
    school = cast(School, SchoolFactory())
    learner, _, _ = create_medical_context(school)
    membership = cast(
        Membership,
        MembershipFactory(school=school, role_code=role_code),
    )

    assert not can_view_medical_record(membership.user, school, learner)
    with pytest.raises(PermissionDenied):
        access_medical_record(membership.user, school, learner)
