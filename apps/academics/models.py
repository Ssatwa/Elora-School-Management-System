from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import TimeStampedModel, UUIDModel
from apps.tenancy.managers import TenantManager


class AcademicYear(UUIDModel, TimeStampedModel):
    class Status(models.TextChoices):
        PLANNED = "planned", "Planned"
        ACTIVE = "active", "Active"
        CLOSED = "closed", "Closed"

    school = models.ForeignKey(
        "tenancy.School",
        on_delete=models.CASCADE,
        related_name="academic_years",
    )
    name = models.CharField(max_length=40)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PLANNED,
    )

    objects = TenantManager()

    class Meta:
        ordering = ["-start_date"]
        constraints = [
            models.UniqueConstraint(
                fields=["school", "name"],
                name="unique_academic_year_name_per_school",
            )
        ]
        indexes = [
            models.Index(fields=["school", "status", "start_date"]),
        ]

    def clean(self):
        super().clean()
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError({"end_date": "The end date must follow the start date."})

    def __str__(self):
        return self.name


class Term(UUIDModel, TimeStampedModel):
    school = models.ForeignKey(
        "tenancy.School",
        on_delete=models.CASCADE,
        related_name="terms",
    )
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.PROTECT,
        related_name="terms",
    )
    name = models.CharField(max_length=40)
    sequence = models.PositiveSmallIntegerField()
    start_date = models.DateField()
    end_date = models.DateField()

    objects = TenantManager()

    class Meta:
        ordering = ["academic_year", "sequence"]
        constraints = [
            models.UniqueConstraint(
                fields=["school", "academic_year", "sequence"],
                name="unique_term_sequence_per_academic_year",
            ),
            models.UniqueConstraint(
                fields=["school", "academic_year", "name"],
                name="unique_term_name_per_academic_year",
            ),
        ]
        indexes = [
            models.Index(fields=["school", "start_date", "end_date"]),
        ]

    def clean(self):
        super().clean()
        errors = {}
        if self.academic_year_id and self.school_id != self.academic_year.school_id:
            errors["academic_year"] = "Academic year must belong to the same school."
        if self.start_date and self.end_date and self.end_date < self.start_date:
            errors["end_date"] = "The end date must follow the start date."
        if (
            self.academic_year_id
            and self.start_date
            and self.end_date
            and (
                self.start_date < self.academic_year.start_date
                or self.end_date > self.academic_year.end_date
            )
        ):
            errors["start_date"] = "Term dates must fit inside the academic year."
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.academic_year} - {self.name}"


class Grade(UUIDModel, TimeStampedModel):
    class EducationLevel(models.TextChoices):
        PRE_PRIMARY = "pre_primary", "Pre-primary"
        PRIMARY = "primary", "Primary"
        JUNIOR_SCHOOL = "junior_school", "Junior school"
        SENIOR_SCHOOL = "senior_school", "Senior school"

    school = models.ForeignKey(
        "tenancy.School",
        on_delete=models.CASCADE,
        related_name="grades",
    )
    code = models.SlugField(max_length=32)
    name = models.CharField(max_length=80)
    education_level = models.CharField(max_length=24, choices=EducationLevel.choices)
    order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    objects = TenantManager()

    class Meta:
        ordering = ["order", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["school", "code"],
                name="unique_grade_code_per_school",
            ),
            models.UniqueConstraint(
                fields=["school", "name"],
                name="unique_grade_name_per_school",
            ),
        ]
        indexes = [
            models.Index(fields=["school", "is_active", "order"]),
        ]

    def __str__(self):
        return self.name


class Stream(UUIDModel, TimeStampedModel):
    school = models.ForeignKey(
        "tenancy.School",
        on_delete=models.CASCADE,
        related_name="streams",
    )
    grade = models.ForeignKey(
        Grade,
        on_delete=models.PROTECT,
        related_name="streams",
    )
    code = models.SlugField(max_length=32)
    name = models.CharField(max_length=80)
    is_active = models.BooleanField(default=True)

    objects = TenantManager()

    class Meta:
        ordering = ["grade__order", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["school", "grade", "code"],
                name="unique_stream_code_per_grade",
            ),
            models.UniqueConstraint(
                fields=["school", "grade", "name"],
                name="unique_stream_name_per_grade",
            ),
        ]
        indexes = [
            models.Index(fields=["school", "is_active"]),
        ]

    def clean(self):
        super().clean()
        if self.grade_id and self.school_id != self.grade.school_id:
            raise ValidationError({"grade": "Grade must belong to the same school."})

    def __str__(self):
        return f"{self.grade} {self.name}"
