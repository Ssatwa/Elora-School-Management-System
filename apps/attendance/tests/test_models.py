from datetime import date

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from apps.academics.models import Grade, Stream
from apps.attendance.models import (
    AttendanceCorrection,
    AttendanceRegister,
    LearnerAttendanceEntry,
    StaffAttendanceEntry,
)
from apps.learners.models import Learner
from apps.staff.models import TeacherProfile
from tests.factories import MembershipFactory, SchoolFactory

pytestmark = pytest.mark.django_db


def make_stream(school, suffix=""):
    grade = Grade.objects.create(
        school=school,
        code=f"grade-4{suffix}",
        name=f"Grade 4{suffix}",
        education_level=Grade.EducationLevel.PRIMARY,
        order=4,
    )
    return Stream.objects.create(
        school=school,
        grade=grade,
        code=f"north{suffix}",
        name=f"North{suffix}",
    )


def make_learner(school, admission_number="2026-0001"):
    return Learner.objects.create(
        school=school,
        admission_number=admission_number,
        first_name="Amani",
        last_name="Otieno",
        date_of_birth=date(2015, 3, 2),
        gender=Learner.Gender.FEMALE,
        admission_date=date(2026, 1, 6),
    )


def make_teacher(school, employee_number="T-001"):
    membership = MembershipFactory(school=school, role_code="teacher")
    return TeacherProfile.objects.create(
        school=school,
        membership=membership,
        employee_number=employee_number,
        employment_date=date(2024, 1, 8),
    )


def test_learner_register_requires_stream_from_same_school():
    first = SchoolFactory()
    second = SchoolFactory(slug="second-attendance")
    register = AttendanceRegister(
        school=first,
        attendance_date=date(2026, 6, 13),
        session=AttendanceRegister.Session.MORNING,
        subject_type=AttendanceRegister.SubjectType.LEARNER,
        stream=make_stream(second, "-second"),
    )

    with pytest.raises(ValidationError, match="same school"):
        register.full_clean()


def test_register_target_rules_require_stream_only_for_learner_registers():
    school = SchoolFactory()

    learner_register = AttendanceRegister(
        school=school,
        attendance_date=date(2026, 6, 13),
        session=AttendanceRegister.Session.MORNING,
        subject_type=AttendanceRegister.SubjectType.LEARNER,
    )
    with pytest.raises(ValidationError, match="Stream is required"):
        learner_register.full_clean()

    staff_register = AttendanceRegister(
        school=school,
        attendance_date=date(2026, 6, 13),
        session=AttendanceRegister.Session.MORNING,
        subject_type=AttendanceRegister.SubjectType.STAFF,
        stream=make_stream(school),
    )
    with pytest.raises(ValidationError, match="must not have a stream"):
        staff_register.full_clean()


def test_duplicate_learner_register_is_prevented():
    school = SchoolFactory()
    stream = make_stream(school)
    values = {
        "school": school,
        "attendance_date": date(2026, 6, 13),
        "session": AttendanceRegister.Session.MORNING,
        "subject_type": AttendanceRegister.SubjectType.LEARNER,
        "stream": stream,
    }
    AttendanceRegister.objects.create(**values)

    with pytest.raises(IntegrityError):
        AttendanceRegister.objects.create(**values)


def test_entry_requires_target_from_register_school_and_matching_register_type():
    first = SchoolFactory()
    second = SchoolFactory(slug="second-entry")
    register = AttendanceRegister.objects.create(
        school=first,
        attendance_date=date(2026, 6, 13),
        session=AttendanceRegister.Session.MORNING,
        subject_type=AttendanceRegister.SubjectType.LEARNER,
        stream=make_stream(first),
    )
    learner_entry = LearnerAttendanceEntry(
        school=first,
        register=register,
        learner=make_learner(second),
        status=LearnerAttendanceEntry.Status.PRESENT,
    )
    with pytest.raises(ValidationError, match="same school"):
        learner_entry.full_clean()

    teacher_entry = StaffAttendanceEntry(
        school=first,
        register=register,
        teacher=make_teacher(first),
        status=StaffAttendanceEntry.Status.PRESENT,
    )
    with pytest.raises(ValidationError, match="staff register"):
        teacher_entry.full_clean()


def test_duplicate_entry_per_register_is_prevented():
    school = SchoolFactory()
    learner = make_learner(school)
    register = AttendanceRegister.objects.create(
        school=school,
        attendance_date=date(2026, 6, 13),
        session=AttendanceRegister.Session.MORNING,
        subject_type=AttendanceRegister.SubjectType.LEARNER,
        stream=make_stream(school),
    )
    values = {
        "school": school,
        "register": register,
        "learner": learner,
        "status": LearnerAttendanceEntry.Status.PRESENT,
    }
    LearnerAttendanceEntry.objects.create(**values)

    with pytest.raises(IntegrityError):
        LearnerAttendanceEntry.objects.create(**values)


def test_correction_requires_exactly_one_entry_and_matching_status_history():
    school = SchoolFactory()
    learner_entry = LearnerAttendanceEntry.objects.create(
        school=school,
        register=AttendanceRegister.objects.create(
            school=school,
            attendance_date=date(2026, 6, 13),
            session=AttendanceRegister.Session.MORNING,
            subject_type=AttendanceRegister.SubjectType.LEARNER,
            stream=make_stream(school),
        ),
        learner=make_learner(school),
        status=LearnerAttendanceEntry.Status.ABSENT,
    )
    invalid = AttendanceCorrection(
        school=school,
        old_status=LearnerAttendanceEntry.Status.ABSENT,
        new_status=LearnerAttendanceEntry.Status.PRESENT,
        reason="Verified at reception",
    )
    with pytest.raises(ValidationError, match="exactly one"):
        invalid.full_clean()

    correction = AttendanceCorrection(
        school=school,
        learner_entry=learner_entry,
        old_status=LearnerAttendanceEntry.Status.ABSENT,
        new_status=LearnerAttendanceEntry.Status.PRESENT,
        reason="Verified at reception",
    )
    correction.full_clean()
