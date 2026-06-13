from datetime import date

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

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
from apps.learners.models import (
    Enrollment,
    Guardian,
    Learner,
    LearnerGuardian,
    MedicalRecord,
)
from apps.staff.models import Department, StaffAssignment, TeacherProfile
from apps.tenancy.models import School, SchoolDomain

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
        for name, sequence, start_date, end_date in term_dates:
            Term.objects.update_or_create(
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
