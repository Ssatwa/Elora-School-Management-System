from datetime import date
from typing import cast

import pytest

from apps.academics.models import (
    AcademicYear,
    Competency,
    Grade,
    LearningArea,
    LearningOutcome,
    OutcomeCompetency,
    Strand,
    Stream,
    SubStrand,
)
from apps.accounts.models import Membership, User
from apps.learners.models import AdmissionApplication, Enrollment, Learner
from apps.learners.services.admissions import admit_learner
from apps.learners.services.transfers import transfer_learner
from apps.staff.models import Department, StaffAssignment, TeacherProfile
from apps.staff.services import assign_staff
from apps.tenancy.models import School
from tests.factories import MembershipFactory, SchoolFactory, UserFactory

pytestmark = pytest.mark.django_db


def test_milestone_two_daily_workflow_preserves_history():
    school = cast(School, SchoolFactory())
    actor = cast(User, UserFactory())
    year = AcademicYear.objects.create(
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
    mathematics = LearningArea.objects.create(
        school=school,
        code="MATH",
        name="Mathematics",
    )
    strand = Strand.objects.create(
        school=school,
        learning_area=mathematics,
        grade=grade,
        code="NUM",
        name="Numbers",
    )
    sub_strand = SubStrand.objects.create(
        school=school,
        strand=strand,
        code="WHOLE",
        name="Whole Numbers",
    )
    outcome = LearningOutcome.objects.create(
        school=school,
        sub_strand=sub_strand,
        code="MATH-G7-NUM-01",
        description="Represent and compare whole numbers.",
    )
    competency = Competency.objects.create(
        school=school,
        code="CTPS",
        name="Critical Thinking and Problem Solving",
    )
    OutcomeCompetency.objects.create(
        school=school,
        outcome=outcome,
        competency=competency,
    )

    teacher_membership = cast(
        Membership,
        MembershipFactory(school=school, role_code="teacher"),
    )
    teacher = TeacherProfile.objects.create(
        school=school,
        membership=teacher_membership,
        employee_number="EMP-001",
        employment_date=date(2024, 1, 8),
    )
    department = Department.objects.create(
        school=school,
        code="SCI",
        name="Sciences",
    )
    assign_staff(
        school=school,
        actor=actor,
        teacher=teacher,
        department=department,
        learning_area=mathematics,
        grade=grade,
        stream=stream,
        role=StaffAssignment.Role.SUBJECT_TEACHER,
        start_date=date(2026, 1, 1),
        weekly_lessons=5,
    )

    application = AdmissionApplication.objects.create(
        school=school,
        first_name="Amina",
        last_name="Kamau",
        date_of_birth=date(2013, 6, 12),
        gender=Learner.Gender.FEMALE,
        desired_grade=grade,
        submitted_at=date(2025, 11, 3),
    )
    learner = admit_learner(
        school=school,
        actor=actor,
        application=application,
        academic_year=year,
        grade=grade,
        stream=stream,
        admission_date=date(2026, 1, 6),
        learner_data={},
        guardians=[
            {
                "first_name": "Wanjiku",
                "last_name": "Kamau",
                "email": "parent@example.test",
                "phone_number": "+254700000001",
                "relationship": "mother",
                "is_primary": True,
            }
        ],
        medical_data={"blood_group": "O+"},
    )
    original_enrollment = Enrollment.objects.get(learner=learner)

    transfer_learner(
        school=school,
        actor=actor,
        learner=learner,
        destination_school_name="Lakeview Academy",
        transfer_date=date(2026, 6, 30),
        reason="Family relocation",
    )

    original_enrollment.refresh_from_db()
    learner.refresh_from_db()
    assert learner.status == Learner.Status.TRANSFERRED
    assert original_enrollment.status == Enrollment.Status.TRANSFERRED
    assert original_enrollment.end_date == date(2026, 6, 30)
    assert learner.guardian_links.count() == 1
    assert outcome.competencies.get() == competency
    assert teacher.current_weekly_lessons == 5
