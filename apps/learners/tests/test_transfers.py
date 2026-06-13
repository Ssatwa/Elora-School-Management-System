from datetime import date
from typing import cast

import pytest
from django.core.exceptions import ValidationError

from apps.academics.models import AcademicYear, Grade, Stream
from apps.accounts.models import AuditLog, User
from apps.learners.models import Enrollment, Learner, TransferRecord
from apps.learners.services.transfers import transfer_learner
from apps.tenancy.models import School
from tests.factories import SchoolFactory, UserFactory

pytestmark = pytest.mark.django_db


def create_enrolled_learner(school: School):
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
    enrollment = Enrollment.objects.create(
        school=school,
        learner=learner,
        academic_year=academic_year,
        grade=grade,
        stream=stream,
        start_date=date(2026, 1, 6),
    )
    return learner, enrollment


def test_transfer_closes_enrollment_and_preserves_history():
    school = cast(School, SchoolFactory())
    actor = cast(User, UserFactory())
    learner, enrollment = create_enrolled_learner(school)

    transfer = transfer_learner(
        school=school,
        actor=actor,
        learner=learner,
        destination_school_name="Lakeview Academy",
        transfer_date=date(2026, 6, 30),
        reason="Family relocation",
        export_reference="EXP-2026-0001",
    )

    learner.refresh_from_db()
    enrollment.refresh_from_db()
    assert transfer.status == TransferRecord.Status.COMPLETED
    assert learner.status == Learner.Status.TRANSFERRED
    assert enrollment.status == Enrollment.Status.TRANSFERRED
    assert enrollment.end_date == date(2026, 6, 30)
    assert learner.enrollments.get() == enrollment
    assert AuditLog.objects.filter(
        action="learners.transfer.completed",
        target_id=str(transfer.id),
    ).exists()


def test_transfer_without_active_enrollment_changes_nothing():
    school = cast(School, SchoolFactory())
    actor = cast(User, UserFactory())
    learner, enrollment = create_enrolled_learner(school)
    enrollment.status = Enrollment.Status.COMPLETED
    enrollment.end_date = date(2026, 5, 1)
    enrollment.save(update_fields=["status", "end_date", "updated_at"])

    with pytest.raises(ValidationError, match="active enrollment"):
        transfer_learner(
            school=school,
            actor=actor,
            learner=learner,
            destination_school_name="Lakeview Academy",
            transfer_date=date(2026, 6, 30),
            reason="Family relocation",
        )

    learner.refresh_from_db()
    assert learner.status == Learner.Status.ACTIVE
    assert TransferRecord.objects.count() == 0
    assert AuditLog.objects.filter(action="learners.transfer.completed").count() == 0


def test_transfer_rejects_learner_from_another_school():
    first_school = cast(School, SchoolFactory())
    second_school = cast(School, SchoolFactory())
    actor = cast(User, UserFactory())
    learner, _ = create_enrolled_learner(second_school)

    with pytest.raises(ValidationError, match="same school"):
        transfer_learner(
            school=first_school,
            actor=actor,
            learner=learner,
            destination_school_name="Lakeview Academy",
            transfer_date=date(2026, 6, 30),
            reason="Family relocation",
        )
