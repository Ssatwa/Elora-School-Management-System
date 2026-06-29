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


class StreamLabel(UUIDModel, TimeStampedModel):
    school = models.ForeignKey(
        "tenancy.School",
        on_delete=models.CASCADE,
        related_name="stream_labels",
    )
    code = models.SlugField(max_length=32)
    name = models.CharField(max_length=80)
    is_active = models.BooleanField(default=True)

    objects = TenantManager()

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["school", "code"],
                name="unique_stream_label_code_per_school",
            ),
            models.UniqueConstraint(
                fields=["school", "name"],
                name="unique_stream_label_name_per_school",
            ),
        ]
        indexes = [
            models.Index(fields=["school", "is_active", "name"]),
        ]

    def __str__(self):
        return self.name


class LearningArea(UUIDModel, TimeStampedModel):
    school = models.ForeignKey(
        "tenancy.School",
        on_delete=models.CASCADE,
        related_name="learning_areas",
    )
    code = models.SlugField(max_length=40)
    name = models.CharField(max_length=120)
    is_active = models.BooleanField(default=True)

    objects = TenantManager()

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["school", "code"],
                name="unique_learning_area_code_per_school",
            ),
            models.UniqueConstraint(
                fields=["school", "name"],
                name="unique_learning_area_name_per_school",
            ),
        ]
        indexes = [
            models.Index(fields=["school", "is_active", "name"]),
        ]

    def __str__(self):
        return self.name


class Strand(UUIDModel, TimeStampedModel):
    school = models.ForeignKey(
        "tenancy.School",
        on_delete=models.CASCADE,
        related_name="strands",
    )
    learning_area = models.ForeignKey(
        LearningArea,
        on_delete=models.PROTECT,
        related_name="strands",
    )
    grade = models.ForeignKey(
        Grade,
        on_delete=models.PROTECT,
        related_name="strands",
    )
    code = models.SlugField(max_length=50)
    name = models.CharField(max_length=160)

    objects = TenantManager()

    class Meta:
        ordering = ["learning_area__name", "grade__order", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["school", "learning_area", "grade", "code"],
                name="unique_strand_code_per_area_grade",
            )
        ]
        indexes = [
            models.Index(fields=["school", "learning_area", "grade"]),
        ]

    def clean(self):
        super().clean()
        if (
            self.learning_area_id
            and self.grade_id
            and (
                self.school_id != self.learning_area.school_id
                or self.school_id != self.grade.school_id
            )
        ):
            raise ValidationError(
                {"learning_area": "Learning area and grade must belong to the same school."}
            )

    def __str__(self):
        return self.name


class SubStrand(UUIDModel, TimeStampedModel):
    school = models.ForeignKey(
        "tenancy.School",
        on_delete=models.CASCADE,
        related_name="sub_strands",
    )
    strand = models.ForeignKey(
        Strand,
        on_delete=models.PROTECT,
        related_name="sub_strands",
    )
    code = models.SlugField(max_length=60)
    name = models.CharField(max_length=180)

    objects = TenantManager()

    class Meta:
        ordering = ["strand__name", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["school", "strand", "code"],
                name="unique_sub_strand_code_per_strand",
            )
        ]
        indexes = [
            models.Index(fields=["school", "strand"]),
        ]

    def clean(self):
        super().clean()
        if self.strand_id and self.school_id != self.strand.school_id:
            raise ValidationError({"strand": "Strand must belong to the same school."})

    def __str__(self):
        return self.name


class LearningOutcome(UUIDModel, TimeStampedModel):
    school = models.ForeignKey(
        "tenancy.School",
        on_delete=models.CASCADE,
        related_name="learning_outcomes",
    )
    sub_strand = models.ForeignKey(
        SubStrand,
        on_delete=models.PROTECT,
        related_name="learning_outcomes",
    )
    code = models.SlugField(max_length=80)
    description = models.TextField()
    competencies: models.ManyToManyField = models.ManyToManyField(
        "Competency",
        through="OutcomeCompetency",
        related_name="learning_outcomes",
    )

    objects = TenantManager()

    class Meta:
        ordering = ["code"]
        constraints = [
            models.UniqueConstraint(
                fields=["school", "code"],
                name="unique_learning_outcome_code_per_school",
            )
        ]
        indexes = [
            models.Index(fields=["school", "sub_strand"]),
        ]

    def clean(self):
        super().clean()
        if self.sub_strand_id and self.school_id != self.sub_strand.school_id:
            raise ValidationError({"sub_strand": "Sub-strand must belong to the same school."})

    def __str__(self):
        return self.code


class Competency(UUIDModel, TimeStampedModel):
    school = models.ForeignKey(
        "tenancy.School",
        on_delete=models.CASCADE,
        related_name="competencies",
    )
    code = models.SlugField(max_length=40)
    name = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    objects = TenantManager()

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["school", "code"],
                name="unique_competency_code_per_school",
            ),
            models.UniqueConstraint(
                fields=["school", "name"],
                name="unique_competency_name_per_school",
            ),
        ]
        indexes = [
            models.Index(fields=["school", "is_active", "name"]),
        ]

    def __str__(self):
        return self.name


class OutcomeCompetency(UUIDModel, TimeStampedModel):
    school = models.ForeignKey(
        "tenancy.School",
        on_delete=models.CASCADE,
        related_name="outcome_competencies",
    )
    outcome = models.ForeignKey(
        LearningOutcome,
        on_delete=models.CASCADE,
        related_name="competency_links",
    )
    competency = models.ForeignKey(
        Competency,
        on_delete=models.CASCADE,
        related_name="outcome_links",
    )

    objects = TenantManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["school", "outcome", "competency"],
                name="unique_outcome_competency_link",
            )
        ]
        indexes = [
            models.Index(fields=["school", "outcome"]),
            models.Index(fields=["school", "competency"]),
        ]

    def clean(self):
        super().clean()
        if (
            self.outcome_id
            and self.competency_id
            and (
                self.school_id != self.outcome.school_id
                or self.school_id != self.competency.school_id
            )
        ):
            raise ValidationError(
                {"competency": "Outcome and competency must belong to the same school."}
            )

    def __str__(self):
        return f"{self.outcome} - {self.competency}"
