from datetime import date
from typing import cast

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from apps.learners.models import Guardian, Learner, LearnerGuardian, MedicalRecord
from apps.tenancy.models import School
from tests.factories import SchoolFactory

pytestmark = pytest.mark.django_db


def create_learner(school: School, admission_number: str = "2026-0001") -> Learner:
    return Learner.objects.create(
        school=school,
        admission_number=admission_number,
        first_name="Amina",
        last_name="Kamau",
        date_of_birth=date(2013, 6, 12),
        gender=Learner.Gender.FEMALE,
        admission_date=date(2026, 1, 6),
    )


def create_guardian(school: School, email: str = "parent@example.test") -> Guardian:
    return Guardian.objects.create(
        school=school,
        first_name="Wanjiku",
        last_name="Kamau",
        email=email,
        phone_number="+254700000001",
    )


def test_admission_number_is_unique_per_school():
    school = cast(School, SchoolFactory())
    create_learner(school)

    with pytest.raises(IntegrityError):
        create_learner(school)


def test_guardian_link_requires_same_school():
    first_school = cast(School, SchoolFactory())
    second_school = cast(School, SchoolFactory())
    link = LearnerGuardian(
        school=first_school,
        learner=create_learner(first_school),
        guardian=create_guardian(second_school),
        relationship=LearnerGuardian.Relationship.MOTHER,
    )

    with pytest.raises(ValidationError, match="same school"):
        link.full_clean()


def test_learner_has_only_one_primary_guardian():
    school = cast(School, SchoolFactory())
    learner = create_learner(school)
    LearnerGuardian.objects.create(
        school=school,
        learner=learner,
        guardian=create_guardian(school),
        relationship=LearnerGuardian.Relationship.MOTHER,
        is_primary=True,
    )

    with pytest.raises(IntegrityError):
        LearnerGuardian.objects.create(
            school=school,
            learner=learner,
            guardian=create_guardian(school, email="second@example.test"),
            relationship=LearnerGuardian.Relationship.FATHER,
            is_primary=True,
        )


def test_medical_record_requires_learner_from_same_school():
    first_school = cast(School, SchoolFactory())
    second_school = cast(School, SchoolFactory())
    record = MedicalRecord(
        school=second_school,
        learner=create_learner(first_school),
        blood_group="O+",
        allergies="Peanuts",
    )

    with pytest.raises(ValidationError, match="same school"):
        record.full_clean()


def test_learner_records_are_explicitly_school_scoped():
    first_school = cast(School, SchoolFactory())
    second_school = cast(School, SchoolFactory())
    create_learner(first_school)
    create_learner(second_school)

    assert Learner.objects.for_school(first_school).count() == 1
    assert Learner.objects.for_school(second_school).count() == 1
