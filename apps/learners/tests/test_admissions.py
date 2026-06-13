from datetime import date
from typing import cast

import pytest
from django.core.exceptions import ValidationError

from apps.academics.models import AcademicYear, Grade, Stream
from apps.accounts.models import AuditLog, User
from apps.learners.models import (
    AdmissionApplication,
    Enrollment,
    Guardian,
    Learner,
    MedicalRecord,
)
from apps.learners.services.admissions import admit_learner
from apps.tenancy.models import School
from tests.factories import SchoolFactory, UserFactory

pytestmark = pytest.mark.django_db


def create_academic_context(school: School):
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
    return academic_year, grade, stream


def create_application(school: School, desired_grade: Grade):
    return AdmissionApplication.objects.create(
        school=school,
        first_name="Amina",
        last_name="Kamau",
        date_of_birth=date(2013, 6, 12),
        gender=Learner.Gender.FEMALE,
        desired_grade=desired_grade,
        submitted_at=date(2025, 11, 3),
    )


def test_admission_creates_complete_audited_record():
    school = cast(School, SchoolFactory())
    actor = cast(User, UserFactory())
    academic_year, grade, stream = create_academic_context(school)
    application = create_application(school, grade)

    learner = admit_learner(
        school=school,
        actor=actor,
        application=application,
        academic_year=academic_year,
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
        medical_data={"blood_group": "O+", "allergies": "Peanuts"},
    )

    application.refresh_from_db()
    assert learner.admission_number == "2026-0001"
    assert learner.guardian_links.select_related("guardian").get().guardian.email == (
        "parent@example.test"
    )
    assert MedicalRecord.objects.get(learner=learner).allergies == "Peanuts"
    assert Enrollment.objects.get(learner=learner).stream == stream
    assert application.status == AdmissionApplication.Status.ADMITTED
    assert AuditLog.objects.filter(
        action="learners.admission.completed",
        target_id=str(learner.id),
    ).exists()


def test_admission_numbers_increment_per_school_and_year():
    school = cast(School, SchoolFactory())
    actor = cast(User, UserFactory())
    academic_year, grade, stream = create_academic_context(school)

    numbers = []
    for index in range(2):
        application = AdmissionApplication.objects.create(
            school=school,
            first_name=f"Learner {index}",
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
            academic_year=academic_year,
            grade=grade,
            stream=stream,
            admission_date=date(2026, 1, 6),
            learner_data={},
            guardians=[],
            medical_data={},
        )
        numbers.append(learner.admission_number)

    assert numbers == ["2026-0001", "2026-0002"]


def test_invalid_cross_school_placement_rolls_back_entire_admission():
    first_school = cast(School, SchoolFactory())
    second_school = cast(School, SchoolFactory())
    actor = cast(User, UserFactory())
    academic_year, grade, _ = create_academic_context(first_school)
    _, second_grade, second_stream = create_academic_context(second_school)
    application = create_application(first_school, grade)

    with pytest.raises(ValidationError, match="same school"):
        admit_learner(
            school=first_school,
            actor=actor,
            application=application,
            academic_year=academic_year,
            grade=second_grade,
            stream=second_stream,
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

    application.refresh_from_db()
    assert application.status == AdmissionApplication.Status.SUBMITTED
    assert Learner.objects.count() == 0
    assert Guardian.objects.count() == 0
    assert Enrollment.objects.count() == 0
    assert MedicalRecord.objects.count() == 0
    assert AuditLog.objects.filter(action="learners.admission.completed").count() == 0
