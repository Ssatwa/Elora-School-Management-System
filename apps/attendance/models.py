from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from apps.core.models import TimeStampedModel, UUIDModel
from apps.tenancy.managers import TenantManager


class AttendanceRegister(UUIDModel, TimeStampedModel):
    class Session(models.TextChoices):
        MORNING = "morning", "Morning"
        AFTERNOON = "afternoon", "Afternoon"

    class SubjectType(models.TextChoices):
        LEARNER = "learner", "Learner"
        STAFF = "staff", "Staff"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        COMPLETED = "completed", "Completed"

    school = models.ForeignKey(
        "tenancy.School",
        on_delete=models.CASCADE,
        related_name="attendance_registers",
    )
    attendance_date = models.DateField()
    session = models.CharField(max_length=16, choices=Session.choices)
    subject_type = models.CharField(max_length=16, choices=SubjectType.choices)
    stream = models.ForeignKey(
        "academics.Stream",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="attendance_registers",
    )
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT)
    marked_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="marked_attendance_registers",
    )
    completed_at = models.DateTimeField(null=True, blank=True)

    objects = TenantManager()

    class Meta:
        ordering = ["-attendance_date", "session", "subject_type"]
        constraints = [
            models.UniqueConstraint(
                fields=["school", "attendance_date", "session", "stream"],
                condition=Q(subject_type="learner"),
                name="unique_learner_attendance_register",
            ),
            models.UniqueConstraint(
                fields=["school", "attendance_date", "session"],
                condition=Q(subject_type="staff"),
                name="unique_staff_attendance_register",
            ),
        ]
        indexes = [
            models.Index(fields=["school", "attendance_date", "subject_type"]),
            models.Index(fields=["school", "status", "attendance_date"]),
        ]

    def clean(self):
        super().clean()
        errors = {}
        stream = self.stream
        if self.stream_id and stream is not None and self.school_id != stream.school_id:
            errors["stream"] = "Stream must belong to the same school."
        if self.subject_type == self.SubjectType.LEARNER and not self.stream_id:
            errors["stream"] = "Stream is required for learner registers."
        if self.subject_type == self.SubjectType.STAFF and self.stream_id:
            errors["stream"] = "Staff registers must not have a stream."
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        target = self.stream or self.get_subject_type_display()
        return f"{self.attendance_date} {self.get_session_display()} - {target}"


class AttendanceEntryBase(UUIDModel, TimeStampedModel):
    class Status(models.TextChoices):
        PRESENT = "present", "Present"
        ABSENT = "absent", "Absent"
        LATE = "late", "Late"
        EXCUSED = "excused", "Excused"

    school = models.ForeignKey("tenancy.School", on_delete=models.CASCADE)
    status = models.CharField(max_length=16, choices=Status.choices)
    arrival_time = models.TimeField(null=True, blank=True)
    note = models.CharField(max_length=250, blank=True)

    objects = TenantManager()

    class Meta:
        abstract = True


class LearnerAttendanceEntry(AttendanceEntryBase):
    register = models.ForeignKey(
        AttendanceRegister,
        on_delete=models.PROTECT,
        related_name="learner_entries",
    )
    learner = models.ForeignKey(
        "learners.Learner",
        on_delete=models.PROTECT,
        related_name="attendance_entries",
    )

    class Meta:
        ordering = ["learner__last_name", "learner__first_name"]
        constraints = [
            models.UniqueConstraint(
                fields=["school", "register", "learner"],
                name="unique_learner_attendance_entry",
            )
        ]
        indexes = [
            models.Index(fields=["school", "learner", "status"]),
            models.Index(fields=["school", "register"]),
        ]

    def clean(self):
        super().clean()
        errors = {}
        if self.register_id and self.school_id != self.register.school_id:
            errors["register"] = "Register must belong to the same school."
        if self.learner_id and self.school_id != self.learner.school_id:
            errors["learner"] = "Learner must belong to the same school."
        if (
            self.register_id
            and self.register.subject_type != AttendanceRegister.SubjectType.LEARNER
        ):
            errors["register"] = "Learner entries require a learner register."
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.learner} - {self.get_status_display()}"


class StaffAttendanceEntry(AttendanceEntryBase):
    register = models.ForeignKey(
        AttendanceRegister,
        on_delete=models.PROTECT,
        related_name="staff_entries",
    )
    teacher = models.ForeignKey(
        "staff.TeacherProfile",
        on_delete=models.PROTECT,
        related_name="attendance_entries",
    )

    class Meta:
        ordering = ["teacher__employee_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["school", "register", "teacher"],
                name="unique_staff_attendance_entry",
            )
        ]
        indexes = [
            models.Index(fields=["school", "teacher", "status"]),
            models.Index(fields=["school", "register"]),
        ]

    def clean(self):
        super().clean()
        errors = {}
        if self.register_id and self.school_id != self.register.school_id:
            errors["register"] = "Register must belong to the same school."
        if self.teacher_id and self.school_id != self.teacher.school_id:
            errors["teacher"] = "Teacher must belong to the same school."
        if (
            self.register_id
            and self.register.subject_type != AttendanceRegister.SubjectType.STAFF
        ):
            errors["register"] = "Staff entries require a staff register."
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.teacher} - {self.get_status_display()}"


class AttendanceCorrection(UUIDModel):
    school = models.ForeignKey(
        "tenancy.School",
        on_delete=models.CASCADE,
        related_name="attendance_corrections",
    )
    learner_entry = models.ForeignKey(
        LearnerAttendanceEntry,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="corrections",
    )
    staff_entry = models.ForeignKey(
        StaffAttendanceEntry,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="corrections",
    )
    old_status = models.CharField(max_length=16, choices=AttendanceEntryBase.Status.choices)
    new_status = models.CharField(max_length=16, choices=AttendanceEntryBase.Status.choices)
    old_arrival_time = models.TimeField(null=True, blank=True)
    new_arrival_time = models.TimeField(null=True, blank=True)
    old_note = models.CharField(max_length=250, blank=True)
    new_note = models.CharField(max_length=250, blank=True)
    reason = models.TextField()
    corrected_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="attendance_corrections",
    )
    corrected_at = models.DateTimeField(auto_now_add=True)

    objects = TenantManager()

    class Meta:
        ordering = ["-corrected_at"]
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(learner_entry__isnull=False, staff_entry__isnull=True)
                    | Q(learner_entry__isnull=True, staff_entry__isnull=False)
                ),
                name="attendance_correction_has_one_entry",
            )
        ]
        indexes = [models.Index(fields=["school", "corrected_at"])]

    def clean(self):
        super().clean()
        targets = [self.learner_entry, self.staff_entry]
        if sum(target is not None for target in targets) != 1:
            raise ValidationError("Attendance correction must reference exactly one entry.")
        target = self.learner_entry or self.staff_entry
        if target is not None and target.school_id != self.school_id:
            raise ValidationError({"school": "Entry must belong to the same school."})

    def save(self, *args, **kwargs):
        if self.pk and type(self).objects.filter(pk=self.pk).exists():
            raise ValidationError("Attendance corrections are immutable.")
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.old_status} to {self.new_status}"


class AbsenceAlert(UUIDModel, TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SENT = "sent", "Sent"
        ACKNOWLEDGED = "acknowledged", "Acknowledged"

    school = models.ForeignKey(
        "tenancy.School",
        on_delete=models.CASCADE,
        related_name="absence_alerts",
    )
    learner_entry = models.OneToOneField(
        LearnerAttendanceEntry,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="absence_alert",
    )
    staff_entry = models.OneToOneField(
        StaffAttendanceEntry,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="absence_alert",
    )
    recipient_summary = models.CharField(max_length=250, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    sent_at = models.DateTimeField(null=True, blank=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)

    objects = TenantManager()

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(learner_entry__isnull=False, staff_entry__isnull=True)
                    | Q(learner_entry__isnull=True, staff_entry__isnull=False)
                ),
                name="absence_alert_has_one_entry",
            )
        ]
        indexes = [models.Index(fields=["school", "status", "created_at"])]

    def clean(self):
        super().clean()
        targets = [self.learner_entry, self.staff_entry]
        if sum(target is not None for target in targets) != 1:
            raise ValidationError("Absence alert must reference exactly one entry.")
        target = self.learner_entry or self.staff_entry
        if target is not None and target.school_id != self.school_id:
            raise ValidationError({"school": "Entry must belong to the same school."})

    def __str__(self):
        return f"Absence alert - {self.get_status_display()}"
