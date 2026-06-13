from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import TimeStampedModel, UUIDModel
from apps.tenancy.managers import TenantManager


class Room(UUIDModel, TimeStampedModel):
    school = models.ForeignKey(
        "tenancy.School",
        on_delete=models.CASCADE,
        related_name="rooms",
    )
    code = models.SlugField(max_length=40)
    name = models.CharField(max_length=100)
    capacity = models.PositiveSmallIntegerField()
    is_active = models.BooleanField(default=True)

    objects = TenantManager()

    class Meta:
        ordering = ["code"]
        constraints = [
            models.UniqueConstraint(
                fields=["school", "code"],
                name="unique_room_code_per_school",
            )
        ]
        indexes = [models.Index(fields=["school", "is_active", "code"])]

    def __str__(self):
        return f"{self.code} - {self.name}"


class TimetablePeriod(UUIDModel, TimeStampedModel):
    class Weekday(models.IntegerChoices):
        MONDAY = 1, "Monday"
        TUESDAY = 2, "Tuesday"
        WEDNESDAY = 3, "Wednesday"
        THURSDAY = 4, "Thursday"
        FRIDAY = 5, "Friday"
        SATURDAY = 6, "Saturday"
        SUNDAY = 7, "Sunday"

    school = models.ForeignKey(
        "tenancy.School",
        on_delete=models.CASCADE,
        related_name="timetable_periods",
    )
    weekday = models.PositiveSmallIntegerField(choices=Weekday.choices)
    sequence = models.PositiveSmallIntegerField()
    name = models.CharField(max_length=80)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_break = models.BooleanField(default=False)

    objects = TenantManager()

    class Meta:
        ordering = ["weekday", "sequence"]
        constraints = [
            models.UniqueConstraint(
                fields=["school", "weekday", "sequence"],
                name="unique_timetable_period_sequence",
            )
        ]
        indexes = [models.Index(fields=["school", "weekday", "sequence"])]

    def clean(self):
        super().clean()
        if self.start_time and self.end_time and self.end_time <= self.start_time:
            raise ValidationError({"end_time": "End time must be after start time."})

    def __str__(self):
        return f"{self.get_weekday_display()} {self.name}"


class Timetable(UUIDModel, TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        ARCHIVED = "archived", "Archived"

    school = models.ForeignKey(
        "tenancy.School",
        on_delete=models.CASCADE,
        related_name="timetables",
    )
    academic_year = models.ForeignKey(
        "academics.AcademicYear",
        on_delete=models.PROTECT,
        related_name="timetables",
    )
    term = models.ForeignKey(
        "academics.Term",
        on_delete=models.PROTECT,
        related_name="timetables",
    )
    name = models.CharField(max_length=120)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT)
    published_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="published_timetables",
    )
    published_at = models.DateTimeField(null=True, blank=True)

    objects = TenantManager()

    class Meta:
        ordering = ["-academic_year__start_date", "term__sequence", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["school", "academic_year", "term", "name"],
                name="unique_named_timetable_per_term",
            )
        ]
        indexes = [models.Index(fields=["school", "status", "term"])]

    def clean(self):
        super().clean()
        errors = {}
        if self.academic_year_id and self.school_id != self.academic_year.school_id:
            errors["academic_year"] = "Academic year must belong to the same school."
        if self.term_id and self.school_id != self.term.school_id:
            errors["term"] = "Term must belong to the same school."
        if (
            self.term_id
            and self.academic_year_id
            and self.term.school_id == self.school_id
            and self.term.academic_year_id != self.academic_year_id
        ):
            errors["term"] = "Term must belong to the selected academic year."
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return self.name


class TimetableEntry(UUIDModel, TimeStampedModel):
    school = models.ForeignKey(
        "tenancy.School",
        on_delete=models.CASCADE,
        related_name="timetable_entries",
    )
    timetable = models.ForeignKey(
        Timetable,
        on_delete=models.CASCADE,
        related_name="entries",
    )
    period = models.ForeignKey(
        TimetablePeriod,
        on_delete=models.PROTECT,
        related_name="entries",
    )
    stream = models.ForeignKey(
        "academics.Stream",
        on_delete=models.PROTECT,
        related_name="timetable_entries",
    )
    learning_area = models.ForeignKey(
        "academics.LearningArea",
        on_delete=models.PROTECT,
        related_name="timetable_entries",
    )
    teacher = models.ForeignKey(
        "staff.TeacherProfile",
        on_delete=models.PROTECT,
        related_name="timetable_entries",
    )
    room = models.ForeignKey(
        Room,
        on_delete=models.PROTECT,
        related_name="timetable_entries",
    )

    objects = TenantManager()

    class Meta:
        ordering = ["period__weekday", "period__sequence", "stream__grade__order"]
        indexes = [
            models.Index(fields=["school", "timetable", "period"]),
            models.Index(fields=["school", "teacher", "period"]),
            models.Index(fields=["school", "stream", "period"]),
            models.Index(fields=["school", "room", "period"]),
        ]

    def clean(self):
        super().clean()
        errors = {}
        for field_name in (
            "timetable",
            "period",
            "stream",
            "learning_area",
            "teacher",
            "room",
        ):
            value = getattr(self, field_name)
            if getattr(self, f"{field_name}_id") and value.school_id != self.school_id:
                errors[field_name] = (
                    f"{field_name.replace('_', ' ').title()} must belong to the same school."
                )
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.stream} - {self.learning_area} - {self.period}"
