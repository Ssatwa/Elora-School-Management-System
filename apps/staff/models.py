from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q, Sum
from django.utils import timezone

from apps.core.models import TimeStampedModel, UUIDModel
from apps.tenancy.managers import TenantManager


class TeacherProfile(UUIDModel, TimeStampedModel):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        ON_LEAVE = "on_leave", "On leave"
        INACTIVE = "inactive", "Inactive"

    school = models.ForeignKey(
        "tenancy.School",
        on_delete=models.CASCADE,
        related_name="teacher_profiles",
    )
    membership = models.OneToOneField(
        "accounts.Membership",
        on_delete=models.PROTECT,
        related_name="teacher_profile",
    )
    employee_number = models.CharField(max_length=40)
    tsc_number = models.CharField(max_length=40, blank=True)
    phone_number = models.CharField(max_length=32, blank=True)
    employment_date = models.DateField()
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    objects = TenantManager()

    class Meta:
        ordering = ["employee_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["school", "employee_number"],
                name="unique_teacher_employee_number_per_school",
            ),
            models.UniqueConstraint(
                fields=["school", "tsc_number"],
                condition=~Q(tsc_number=""),
                name="unique_teacher_tsc_number_per_school",
            ),
        ]
        indexes = [
            models.Index(fields=["school", "status", "employee_number"]),
        ]

    def clean(self):
        super().clean()
        if self.membership_id and self.school_id != self.membership.school_id:
            raise ValidationError({"membership": "Membership must belong to the same school."})
        if self.membership_id and not self.membership.is_active:
            raise ValidationError({"membership": "Membership must be active."})

    @property
    def current_weekly_lessons(self):
        today = timezone.localdate()
        return (
            self.assignments.filter(start_date__lte=today)
            .filter(Q(end_date__isnull=True) | Q(end_date__gte=today))
            .aggregate(total=Sum("weekly_lessons"))["total"]
            or 0
        )

    def __str__(self):
        display_name = self.membership.user.get_full_name() or str(self.membership.user)
        return f"{self.employee_number} - {display_name}"


class Department(UUIDModel, TimeStampedModel):
    school = models.ForeignKey(
        "tenancy.School",
        on_delete=models.CASCADE,
        related_name="departments",
    )
    code = models.SlugField(max_length=40)
    name = models.CharField(max_length=120)
    head = models.ForeignKey(
        TeacherProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="headed_departments",
    )
    is_active = models.BooleanField(default=True)

    objects = TenantManager()

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["school", "code"],
                name="unique_department_code_per_school",
            ),
            models.UniqueConstraint(
                fields=["school", "name"],
                name="unique_department_name_per_school",
            ),
        ]
        indexes = [
            models.Index(fields=["school", "is_active", "name"]),
        ]

    def clean(self):
        super().clean()
        head = self.head
        if self.head_id and head is not None and self.school_id != head.school_id:
            raise ValidationError({"head": "Department head must belong to the same school."})

    def __str__(self):
        return self.name


class StaffAssignment(UUIDModel, TimeStampedModel):
    class Role(models.TextChoices):
        SUBJECT_TEACHER = "subject_teacher", "Subject teacher"
        CLASS_TEACHER = "class_teacher", "Class teacher"
        DEPARTMENT_HEAD = "department_head", "Department head"

    school = models.ForeignKey(
        "tenancy.School",
        on_delete=models.CASCADE,
        related_name="staff_assignments",
    )
    teacher = models.ForeignKey(
        TeacherProfile,
        on_delete=models.PROTECT,
        related_name="assignments",
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="staff_assignments",
    )
    learning_area = models.ForeignKey(
        "academics.LearningArea",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="staff_assignments",
    )
    grade = models.ForeignKey(
        "academics.Grade",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="staff_assignments",
    )
    stream = models.ForeignKey(
        "academics.Stream",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="staff_assignments",
    )
    role = models.CharField(max_length=24, choices=Role.choices)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    weekly_lessons = models.PositiveSmallIntegerField(default=0)

    objects = TenantManager()

    class Meta:
        ordering = ["teacher__employee_number", "role", "-start_date"]
        indexes = [
            models.Index(fields=["school", "role", "start_date"]),
            models.Index(fields=["school", "teacher", "end_date"]),
        ]

    def clean(self):
        super().clean()
        errors = {}
        for field_name in ("teacher", "department", "learning_area", "grade", "stream"):
            related_id = getattr(self, f"{field_name}_id")
            if related_id and getattr(self, field_name).school_id != self.school_id:
                label = field_name.replace("_", " ").title()
                errors[field_name] = f"{label} must belong to the same school."
        stream = self.stream
        if (
            self.stream_id
            and stream is not None
            and self.grade_id
            and stream.grade_id != self.grade_id
        ):
            errors["stream"] = "Stream must belong to the selected grade."
        if self.end_date and self.start_date and self.end_date < self.start_date:
            errors["end_date"] = "The end date must follow the start date."
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.teacher} - {self.get_role_display()}"
