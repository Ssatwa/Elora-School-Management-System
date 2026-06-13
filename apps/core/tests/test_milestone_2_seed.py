import pytest
from django.core.management import CommandError, call_command
from django.test import override_settings

from apps.academics.models import (
    AcademicYear,
    Competency,
    Grade,
    LearningArea,
    LearningOutcome,
    Strand,
    Stream,
    SubStrand,
    Term,
)
from apps.learners.models import Enrollment, Guardian, Learner, MedicalRecord
from apps.staff.models import Department, StaffAssignment, TeacherProfile
from apps.tenancy.models import School


@pytest.mark.django_db
def test_seed_demo_creates_idempotent_milestone_two_data_for_two_schools():
    call_command("seed_demo")
    call_command("seed_demo")

    assert School.objects.count() == 2
    for school in School.objects.all():
        assert AcademicYear.objects.for_school(school).count() == 1
        assert Term.objects.for_school(school).count() == 3
        assert Grade.objects.for_school(school).count() >= 2
        assert Stream.objects.for_school(school).count() >= 2
        assert LearningArea.objects.for_school(school).count() >= 2
        assert Strand.objects.for_school(school).exists()
        assert SubStrand.objects.for_school(school).exists()
        assert LearningOutcome.objects.for_school(school).exists()
        assert Competency.objects.for_school(school).exists()
        assert TeacherProfile.objects.for_school(school).count() >= 3
        assert Department.objects.for_school(school).exists()
        assert StaffAssignment.objects.for_school(school).exists()
        assert Learner.objects.for_school(school).exists()
        assert Guardian.objects.for_school(school).exists()
        assert MedicalRecord.objects.for_school(school).exists()
        assert Enrollment.objects.for_school(school).exists()


@override_settings(DEBUG=False, ALLOW_DEMO_SEED=False)
def test_seed_demo_is_blocked_when_not_explicitly_allowed():
    with pytest.raises(CommandError, match="disabled"):
        call_command("seed_demo")
