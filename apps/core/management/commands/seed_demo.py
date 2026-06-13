from datetime import date, time, timedelta
from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

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
    Term,
)
from apps.accounts.models import Membership, Role, User
from apps.accounts.roles import ROLE_DEFINITIONS
from apps.activities.models import ActivityParticipation, Club
from apps.assessments.models import (
    Assessment,
    AssessmentResult,
    CriterionRating,
    RatingLevel,
    Rubric,
    RubricCriterion,
)
from apps.attendance.models import (
    AbsenceAlert,
    AttendanceRegister,
    LearnerAttendanceEntry,
    StaffAttendanceEntry,
)
from apps.communication.models import Announcement, Message, Notification
from apps.finance.models import FeeStructure, Invoice, Payment, PaymentAllocation, Receipt
from apps.learners.models import (
    Enrollment,
    Guardian,
    Learner,
    LearnerGuardian,
    MedicalRecord,
)
from apps.learning.models import Assignment, Resource, Submission
from apps.library.models import BorrowRecord, LibraryBook
from apps.reports.models import ReportCard
from apps.reports.services import (
    create_report_snapshot,
    generate_report_pdf,
    publish_report,
)
from apps.staff.models import Department, StaffAssignment, TeacherProfile
from apps.tenancy.models import School, SchoolDomain
from apps.timetabling.models import Room, Timetable, TimetableEntry, TimetablePeriod
from apps.wellbeing.models import DisciplineRecord

DEMO_SCHOOLS = (
    ("green-hills", "Green Hills Academy"),
    ("sunrise", "Sunrise Academy"),
)
DEMO_PASSWORD = "EloraDemo123!"


class Command(BaseCommand):
    help = "Create deterministic local demo schools, roles, users, and records."

    def handle(self, *args, **options):
        if not settings.ALLOW_DEMO_SEED:
            raise CommandError("Demo seeding is disabled in this environment.")
        roles = self._seed_roles()
        self._seed_platform_user()
        for slug, name in DEMO_SCHOOLS:
            school = self._seed_school(slug, name)
            memberships = self._seed_memberships(school, roles)
            self._seed_school_records(school, memberships)
        self.stdout.write(self.style.SUCCESS("Demo data is ready."))

    def _seed_roles(self):
        roles = {}
        for code, (name, is_platform_role) in ROLE_DEFINITIONS.items():
            roles[code], _ = Role.objects.update_or_create(
                code=code,
                defaults={"name": name, "is_platform_role": is_platform_role},
            )
        return roles

    def _seed_platform_user(self):
        user, created = User.objects.get_or_create(
            email="super_admin@elora.local",
            defaults={"is_staff": True, "is_superuser": True},
        )
        if created:
            user.set_password(DEMO_PASSWORD)
            user.save(update_fields=["password"])

    def _seed_school(self, slug, name):
        school, _ = School.objects.update_or_create(
            slug=slug,
            defaults={"name": name, "is_active": True},
        )
        SchoolDomain.objects.update_or_create(
            hostname=f"{slug}.localhost",
            defaults={"school": school, "is_primary": True},
        )
        return school

    def _seed_memberships(self, school, roles):
        memberships = {}
        for code, (_, is_platform_role) in ROLE_DEFINITIONS.items():
            if is_platform_role:
                continue
            email = f"{code}@{school.slug}.localhost"
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    "first_name": roles[code].name.split()[0],
                    "last_name": "Demo",
                },
            )
            if created:
                user.set_password(DEMO_PASSWORD)
                user.save(update_fields=["password"])
            membership, _ = Membership.objects.get_or_create(
                school=school,
                user=user,
            )
            membership.roles.add(roles[code])
            memberships[code] = membership
        return memberships

    def _seed_school_records(self, school, memberships):
        year, _ = AcademicYear.objects.update_or_create(
            school=school,
            name="2026",
            defaults={
                "start_date": date(2026, 1, 1),
                "end_date": date(2026, 12, 31),
                "status": AcademicYear.Status.ACTIVE,
            },
        )
        term_dates = (
            ("Term 1", 1, date(2026, 1, 6), date(2026, 4, 3)),
            ("Term 2", 2, date(2026, 5, 4), date(2026, 8, 7)),
            ("Term 3", 3, date(2026, 8, 31), date(2026, 11, 27)),
        )
        terms = {}
        for name, sequence, start_date, end_date in term_dates:
            terms[sequence], _ = Term.objects.update_or_create(
                school=school,
                academic_year=year,
                sequence=sequence,
                defaults={
                    "name": name,
                    "start_date": start_date,
                    "end_date": end_date,
                },
            )

        grades = {}
        for code, name, order in (("G7", "Grade 7", 7), ("G8", "Grade 8", 8)):
            grade, _ = Grade.objects.update_or_create(
                school=school,
                code=code,
                defaults={
                    "name": name,
                    "education_level": Grade.EducationLevel.JUNIOR_SCHOOL,
                    "order": order,
                    "is_active": True,
                },
            )
            stream, _ = Stream.objects.update_or_create(
                school=school,
                grade=grade,
                code="E",
                defaults={"name": "East", "is_active": True},
            )
            grades[code] = (grade, stream)

        learning_areas = {}
        for code, name in (
            ("MATH", "Mathematics"),
            ("SCI", "Integrated Science"),
        ):
            learning_areas[code], _ = LearningArea.objects.update_or_create(
                school=school,
                code=code,
                defaults={"name": name, "is_active": True},
            )

        strand, _ = Strand.objects.update_or_create(
            school=school,
            learning_area=learning_areas["MATH"],
            grade=grades["G7"][0],
            code="NUM",
            defaults={"name": "Numbers"},
        )
        sub_strand, _ = SubStrand.objects.update_or_create(
            school=school,
            strand=strand,
            code="WHOLE",
            defaults={"name": "Whole Numbers"},
        )
        outcome, _ = LearningOutcome.objects.update_or_create(
            school=school,
            code="MATH-G7-NUM-01",
            defaults={
                "sub_strand": sub_strand,
                "description": "Represent and compare whole numbers.",
            },
        )
        competency, _ = Competency.objects.update_or_create(
            school=school,
            code="CTPS",
            defaults={
                "name": "Critical Thinking and Problem Solving",
                "description": "Apply reasoning to authentic problems.",
                "is_active": True,
            },
        )
        OutcomeCompetency.objects.get_or_create(
            school=school,
            outcome=outcome,
            competency=competency,
        )

        teacher_profiles = {}
        for index, role_code in enumerate(
            ("teacher", "class_teacher", "department_head"),
            start=1,
        ):
            teacher_profiles[role_code], _ = TeacherProfile.objects.update_or_create(
                membership=memberships[role_code],
                defaults={
                    "school": school,
                    "employee_number": f"{school.slug[:3].upper()}-T{index:03d}",
                    "employment_date": date(2024, 1, 8),
                    "status": TeacherProfile.Status.ACTIVE,
                },
            )
        department, _ = Department.objects.update_or_create(
            school=school,
            code="SCI",
            defaults={
                "name": "Sciences",
                "head": teacher_profiles["department_head"],
                "is_active": True,
            },
        )
        assignment_values = (
            (
                "teacher",
                StaffAssignment.Role.SUBJECT_TEACHER,
                learning_areas["MATH"],
                5,
            ),
            ("class_teacher", StaffAssignment.Role.CLASS_TEACHER, None, 0),
            (
                "department_head",
                StaffAssignment.Role.DEPARTMENT_HEAD,
                learning_areas["SCI"],
                4,
            ),
        )
        for role_code, assignment_role, learning_area, lessons in assignment_values:
            StaffAssignment.objects.update_or_create(
                school=school,
                teacher=teacher_profiles[role_code],
                role=assignment_role,
                grade=grades["G7"][0],
                stream=grades["G7"][1],
                defaults={
                    "department": department,
                    "learning_area": learning_area,
                    "start_date": date(2026, 1, 1),
                    "weekly_lessons": lessons,
                },
            )

        learner, _ = Learner.objects.update_or_create(
            school=school,
            admission_number="2026-0001",
            defaults={
                "membership": memberships["learner"],
                "first_name": "Amina",
                "last_name": "Kamau",
                "date_of_birth": date(2013, 6, 12),
                "gender": Learner.Gender.FEMALE,
                "admission_date": date(2026, 1, 6),
                "status": Learner.Status.ACTIVE,
            },
        )
        guardian, _ = Guardian.objects.update_or_create(
            school=school,
            email=f"parent@{school.slug}.localhost",
            defaults={
                "membership": memberships["parent"],
                "first_name": "Wanjiku",
                "last_name": "Kamau",
                "phone_number": "+254700000001",
            },
        )
        LearnerGuardian.objects.update_or_create(
            school=school,
            learner=learner,
            guardian=guardian,
            defaults={
                "relationship": LearnerGuardian.Relationship.MOTHER,
                "is_primary": True,
                "receives_communication": True,
            },
        )
        MedicalRecord.objects.update_or_create(
            learner=learner,
            defaults={
                "school": school,
                "blood_group": "O+",
                "allergies": "Peanuts",
            },
        )
        Enrollment.objects.update_or_create(
            school=school,
            learner=learner,
            status=Enrollment.Status.ACTIVE,
            defaults={
                "academic_year": year,
                "grade": grades["G7"][0],
                "stream": grades["G7"][1],
                "start_date": date(2026, 1, 6),
            },
        )

        attendance_date = date(2026, 6, 12)
        learner_register, _ = AttendanceRegister.objects.update_or_create(
            school=school,
            attendance_date=attendance_date,
            session=AttendanceRegister.Session.MORNING,
            subject_type=AttendanceRegister.SubjectType.LEARNER,
            stream=grades["G7"][1],
            defaults={
                "status": AttendanceRegister.Status.COMPLETED,
                "marked_by": memberships["class_teacher"].user,
                "completed_at": timezone.now(),
            },
        )
        learner_entry, _ = LearnerAttendanceEntry.objects.update_or_create(
            school=school,
            register=learner_register,
            learner=learner,
            defaults={
                "status": LearnerAttendanceEntry.Status.ABSENT,
                "note": "Guardian notified of absence.",
            },
        )
        AbsenceAlert.objects.update_or_create(
            school=school,
            learner_entry=learner_entry,
            defaults={
                "recipient_summary": guardian.phone_number,
                "status": AbsenceAlert.Status.PENDING,
            },
        )
        staff_register, _ = AttendanceRegister.objects.update_or_create(
            school=school,
            attendance_date=attendance_date,
            session=AttendanceRegister.Session.MORNING,
            subject_type=AttendanceRegister.SubjectType.STAFF,
            defaults={
                "status": AttendanceRegister.Status.COMPLETED,
                "marked_by": memberships["principal"].user,
                "completed_at": timezone.now(),
            },
        )
        StaffAttendanceEntry.objects.update_or_create(
            school=school,
            register=staff_register,
            teacher=teacher_profiles["teacher"],
            defaults={"status": StaffAttendanceEntry.Status.PRESENT},
        )

        rooms = {}
        for code, name in (("R1", "Innovation Room"), ("R2", "Science Lab")):
            rooms[code], _ = Room.objects.update_or_create(
                school=school,
                code=code,
                defaults={"name": name, "capacity": 40, "is_active": True},
            )
        periods = {}
        for sequence, name, start_time, end_time in (
            (1, "Lesson 1", time(8, 0), time(8, 40)),
            (2, "Lesson 2", time(8, 40), time(9, 20)),
            (3, "Lesson 3", time(9, 20), time(10, 0)),
        ):
            periods[sequence], _ = TimetablePeriod.objects.update_or_create(
                school=school,
                weekday=TimetablePeriod.Weekday.MONDAY,
                sequence=sequence,
                defaults={
                    "name": name,
                    "start_time": start_time,
                    "end_time": end_time,
                    "is_break": False,
                },
            )
        timetable, _ = Timetable.objects.update_or_create(
            school=school,
            academic_year=year,
            term=terms[2],
            name="Term 2 master",
            defaults={
                "status": Timetable.Status.PUBLISHED,
                "published_by": memberships["principal"].user,
                "published_at": timezone.now(),
            },
        )
        lesson_values = (
            (
                periods[1],
                learning_areas["MATH"],
                teacher_profiles["teacher"],
                rooms["R1"],
            ),
            (
                periods[2],
                learning_areas["SCI"],
                teacher_profiles["department_head"],
                rooms["R2"],
            ),
        )
        for period, learning_area, teacher, room in lesson_values:
            TimetableEntry.objects.update_or_create(
                school=school,
                timetable=timetable,
                period=period,
                stream=grades["G7"][1],
                defaults={
                    "learning_area": learning_area,
                    "teacher": teacher,
                    "room": room,
                },
            )

        ratings = {}
        for code, name, rank in (
            ("EE", "Exceeding Expectation", 4),
            ("ME", "Meeting Expectation", 3),
            ("AE", "Approaching Expectation", 2),
            ("BE", "Below Expectation", 1),
        ):
            ratings[code], _ = RatingLevel.objects.update_or_create(
                school=school,
                code=code,
                defaults={"name": name, "rank": rank, "is_active": True},
            )
        rubric, _ = Rubric.objects.update_or_create(
            school=school,
            learning_area=learning_areas["MATH"],
            grade=grades["G7"][0],
            name="Whole Numbers CBC Rubric",
            defaults={
                "description": "Measures representation and comparison of whole numbers.",
                "is_active": True,
            },
        )
        criterion, _ = RubricCriterion.objects.update_or_create(
            school=school,
            rubric=rubric,
            outcome=outcome,
            defaults={
                "name": "Represents and compares whole numbers",
                "description": "Uses place value accurately in authentic contexts.",
                "sequence": 1,
            },
        )
        assessment, _ = Assessment.objects.update_or_create(
            school=school,
            term=terms[2],
            stream=grades["G7"][1],
            learning_area=learning_areas["MATH"],
            title="Whole Numbers Performance Task",
            defaults={
                "teacher": teacher_profiles["teacher"],
                "rubric": rubric,
                "assessment_type": Assessment.AssessmentType.FORMATIVE,
                "assessment_date": date(2026, 6, 10),
                "instructions": "Use place value to solve the market-day challenge.",
                "status": Assessment.Status.APPROVED,
                "submitted_at": timezone.now(),
                "moderated_at": timezone.now(),
                "approved_at": timezone.now(),
            },
        )
        result, _ = AssessmentResult.objects.update_or_create(
            school=school,
            assessment=assessment,
            learner=learner,
            defaults={
                "overall_rating": ratings["ME"],
                "teacher_comment": "Amina applies place value confidently.",
                "moderated_comment": "Evidence aligns with the learning outcome.",
                "is_complete": True,
            },
        )
        CriterionRating.objects.update_or_create(
            school=school,
            result=result,
            criterion=criterion,
            defaults={
                "rating": ratings["ME"],
                "comment": "Accurate representations with clear reasoning.",
            },
        )
        report = create_report_snapshot(
            school=school,
            actor=memberships["principal"].user,
            learner=learner,
            term=terms[2],
            principal_remark="Amina is making steady progress. Keep aiming higher.",
        )
        generate_report_pdf(report_id=report.id, school_id=school.id)
        report.refresh_from_db()
        if report.status == ReportCard.Status.READY:
            publish_report(
                school=school,
                actor=memberships["principal"].user,
                report=report,
            )

        FeeStructure.objects.update_or_create(
            school=school,
            term=terms[2],
            grade=grades["G7"][0],
            name="Term 2 Tuition and Activities",
            defaults={"amount": Decimal("25000.00"), "is_active": True},
        )
        invoice, _ = Invoice.objects.update_or_create(
            school=school,
            invoice_number=f"INV-{school.slug.upper()[:4]}-000001",
            defaults={
                "learner": learner,
                "term": terms[2],
                "description": "Term 2 Tuition and Activities",
                "amount": Decimal("25000.00"),
                "due_date": date(2026, 5, 31),
                "status": Invoice.Status.PART_PAID,
                "created_by": memberships["accountant"].user,
            },
        )
        payment, _ = Payment.objects.update_or_create(
            school=school,
            payment_number=f"PAY-{school.slug.upper()[:4]}-000001",
            defaults={
                "learner": learner,
                "amount": Decimal("10000.00"),
                "method": Payment.Method.BANK,
                "reference": f"{school.slug.upper()}-BANK-001",
                "paid_on": date(2026, 5, 15),
                "received_by": memberships["accountant"].user,
            },
        )
        allocation, _ = PaymentAllocation.objects.update_or_create(
            school=school,
            payment=payment,
            invoice=invoice,
            defaults={
                "amount": Decimal("10000.00"),
                "allocated_by": memberships["accountant"].user,
            },
        )
        Receipt.objects.update_or_create(
            school=school,
            receipt_number=f"RCT-{school.slug.upper()[:4]}-000001",
            defaults={
                "allocation": allocation,
                "amount": Decimal("10000.00"),
                "issued_by": memberships["accountant"].user,
            },
        )

        assignment, _ = Assignment.objects.update_or_create(
            school=school,
            teacher=teacher_profiles["teacher"],
            term=terms[2],
            stream=grades["G7"][1],
            learning_area=learning_areas["MATH"],
            title="Number Patterns Home Challenge",
            defaults={
                "instructions": "Complete the number-pattern investigation and explain your rule.",
                "due_at": timezone.now() + timedelta(days=7),
                "is_published": True,
                "published_at": timezone.now(),
            },
        )
        Submission.objects.update_or_create(
            school=school,
            assignment=assignment,
            learner=learner,
            defaults={
                "response": "I found the rule by comparing the difference between terms.",
                "feedback": "Clear reasoning. Add one more example.",
            },
        )
        Resource.objects.update_or_create(
            school=school,
            teacher=teacher_profiles["teacher"],
            learning_area=learning_areas["MATH"],
            title="Understanding Number Patterns",
            defaults={
                "kind": Resource.Kind.NOTE,
                "content": "A concise guide to identifying and explaining number patterns.",
                "is_published": True,
            },
        )
        announcement, _ = Announcement.objects.update_or_create(
            school=school,
            title="Family Learning Afternoon",
            defaults={
                "body": "Parents and guardians are invited on Friday at 2 PM.",
                "published_by": memberships["teacher"].user,
                "published_at": timezone.now(),
            },
        )
        Notification.objects.update_or_create(
            school=school,
            user=memberships["parent"].user,
            announcement=announcement,
            defaults={
                "title": announcement.title,
                "body": announcement.body,
                "delivery_status": "delivered",
            },
        )
        Message.objects.update_or_create(
            school=school,
            sender=memberships["teacher"].user,
            recipient=memberships["parent"].user,
            subject="Amina's mathematics progress",
            defaults={"body": "Amina is participating confidently in number work."},
        )
        book, _ = LibraryBook.objects.update_or_create(
            school=school,
            isbn=f"978-{school.slug[:4]}-0001",
            defaults={
                "title": "CBC Mathematics in Practice",
                "author": "Elora Education Press",
                "category": "Mathematics",
                "total_copies": 8,
                "available_copies": 7,
            },
        )
        BorrowRecord.objects.update_or_create(
            school=school,
            book=book,
            learner=learner,
            status=BorrowRecord.Status.BORROWED,
            defaults={
                "borrowed_by": memberships["librarian"].user,
                "due_date": date(2026, 6, 27),
            },
        )
        DisciplineRecord.objects.update_or_create(
            school=school,
            learner=learner,
            title="Peer support leadership",
            defaults={
                "category": DisciplineRecord.Category.POSITIVE,
                "details": "Helped a new learner settle into the class routine.",
                "action_taken": "Recognized during class meeting.",
                "recorded_by": memberships["guidance_counsellor"].user,
            },
        )
        club, _ = Club.objects.update_or_create(
            school=school,
            name="Robotics and Innovation Club",
            defaults={
                "category": "STEM",
                "patron": memberships["teacher"],
                "meeting_schedule": "Wednesday 3:30 PM",
                "is_active": True,
            },
        )
        ActivityParticipation.objects.update_or_create(
            school=school,
            club=club,
            learner=learner,
            defaults={
                "role": "Design Lead",
                "achievements": "Built a working water-level alert prototype.",
                "is_active": True,
            },
        )
