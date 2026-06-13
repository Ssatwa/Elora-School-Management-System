import pytest
from django.core.management import call_command

from apps.accounts.models import Membership, User
from apps.activities.models import ActivityParticipation, Club
from apps.assessments.models import Assessment, AssessmentResult, RatingLevel
from apps.attendance.models import AttendanceRegister, LearnerAttendanceEntry
from apps.communication.models import Announcement, Notification
from apps.finance.models import Invoice, Payment, Receipt
from apps.learning.models import Assignment, Submission
from apps.library.models import BorrowRecord, LibraryBook
from apps.reports.models import ReportCard
from apps.tenancy.models import School
from apps.timetabling.models import Room, Timetable, TimetableEntry, TimetablePeriod
from apps.wellbeing.models import DisciplineRecord


@pytest.mark.django_db
def test_seed_demo_is_idempotent():
    call_command("seed_demo")
    call_command("seed_demo")

    assert School.objects.filter(slug="green-hills").count() == 1
    assert Membership.objects.filter(school__slug="green-hills").count() == 11
    assert (
        User.objects.filter(
            email="super_admin@elora.local",
            is_superuser=True,
        ).count()
        == 1
    )
    green_hills = School.objects.get(slug="green-hills")
    assert AttendanceRegister.objects.for_school(green_hills).count() == 2
    assert LearnerAttendanceEntry.objects.for_school(green_hills).count() == 1
    assert Room.objects.for_school(green_hills).count() == 2
    assert TimetablePeriod.objects.for_school(green_hills).count() == 3
    assert Timetable.objects.for_school(green_hills).filter(
        status=Timetable.Status.PUBLISHED
    ).count() == 1
    assert TimetableEntry.objects.for_school(green_hills).count() == 2
    assert RatingLevel.objects.for_school(green_hills).count() == 4
    assert Assessment.objects.for_school(green_hills).filter(
        status=Assessment.Status.APPROVED
    ).count() == 1
    assert AssessmentResult.objects.for_school(green_hills).filter(
        is_complete=True
    ).count() == 1
    assert ReportCard.objects.for_school(green_hills).filter(
        status=ReportCard.Status.PUBLISHED
    ).count() == 1
    assert Invoice.objects.for_school(green_hills).count() == 1
    assert Payment.objects.for_school(green_hills).count() == 1
    assert Receipt.objects.for_school(green_hills).count() == 1
    assert Assignment.objects.for_school(green_hills).count() == 1
    assert Submission.objects.for_school(green_hills).count() == 1
    assert Announcement.objects.for_school(green_hills).count() == 1
    assert Notification.objects.for_school(green_hills).count() == 1
    assert LibraryBook.objects.for_school(green_hills).count() == 1
    assert BorrowRecord.objects.for_school(green_hills).count() == 1
    assert DisciplineRecord.objects.for_school(green_hills).count() == 1
    assert Club.objects.for_school(green_hills).count() == 1
    assert ActivityParticipation.objects.for_school(green_hills).count() == 1
