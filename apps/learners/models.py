from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from apps.core.models import TimeStampedModel, UUIDModel
from apps.tenancy.managers import TenantManager


class Learner(UUIDModel, TimeStampedModel):
    class Gender(models.TextChoices):
        FEMALE = "female", "Female"
        MALE = "male", "Male"
        OTHER = "other", "Other"
        NOT_STATED = "not_stated", "Prefer not to say"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        INACTIVE = "inactive", "Inactive"
        TRANSFERRED = "transferred", "Transferred"
        GRADUATED = "graduated", "Graduated"

    school = models.ForeignKey(
        "tenancy.School",
        on_delete=models.CASCADE,
        related_name="learners",
    )
    membership = models.OneToOneField(
        "accounts.Membership",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="learner_profile",
    )
    admission_number = models.CharField(max_length=40)
    first_name = models.CharField(max_length=80)
    middle_name = models.CharField(max_length=80, blank=True)
    last_name = models.CharField(max_length=80)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=16, choices=Gender.choices)
    admission_date = models.DateField()
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    objects = TenantManager()

    class Meta:
        ordering = ["last_name", "first_name", "admission_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["school", "admission_number"],
                name="unique_learner_admission_number_per_school",
            )
        ]
        indexes = [
            models.Index(fields=["school", "status", "last_name"]),
            models.Index(fields=["school", "admission_date"]),
        ]

    @property
    def full_name(self):
        return " ".join(
            part for part in (self.first_name, self.middle_name, self.last_name) if part
        )

    def clean(self):
        super().clean()
        membership = self.membership
        if (
            self.membership_id
            and membership is not None
            and self.school_id != membership.school_id
        ):
            raise ValidationError({"membership": "Membership must belong to the same school."})

    def __str__(self):
        return f"{self.admission_number} - {self.full_name}"


class Guardian(UUIDModel, TimeStampedModel):
    school = models.ForeignKey(
        "tenancy.School",
        on_delete=models.CASCADE,
        related_name="guardians",
    )
    membership = models.ForeignKey(
        "accounts.Membership",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="guardian_profiles",
    )
    first_name = models.CharField(max_length=80)
    last_name = models.CharField(max_length=80)
    email = models.EmailField(blank=True)
    phone_number = models.CharField(max_length=32)
    national_id = models.CharField(max_length=40, blank=True)
    postal_address = models.TextField(blank=True)

    objects = TenantManager()

    class Meta:
        ordering = ["last_name", "first_name"]
        constraints = [
            models.UniqueConstraint(
                fields=["school", "membership"],
                condition=Q(membership__isnull=False),
                name="unique_guardian_membership_per_school",
            ),
            models.UniqueConstraint(
                fields=["school", "email"],
                condition=~Q(email=""),
                name="unique_guardian_email_per_school",
            ),
        ]
        indexes = [
            models.Index(fields=["school", "last_name", "first_name"]),
            models.Index(fields=["school", "phone_number"]),
        ]

    def clean(self):
        super().clean()
        membership = self.membership
        if (
            self.membership_id
            and membership is not None
            and self.school_id != membership.school_id
        ):
            raise ValidationError({"membership": "Membership must belong to the same school."})

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return self.full_name


class LearnerGuardian(UUIDModel, TimeStampedModel):
    class Relationship(models.TextChoices):
        MOTHER = "mother", "Mother"
        FATHER = "father", "Father"
        GUARDIAN = "guardian", "Guardian"
        SIBLING = "sibling", "Sibling"
        OTHER = "other", "Other"

    school = models.ForeignKey(
        "tenancy.School",
        on_delete=models.CASCADE,
        related_name="learner_guardian_links",
    )
    learner = models.ForeignKey(
        Learner,
        on_delete=models.CASCADE,
        related_name="guardian_links",
    )
    guardian = models.ForeignKey(
        Guardian,
        on_delete=models.PROTECT,
        related_name="learner_links",
    )
    relationship = models.CharField(max_length=16, choices=Relationship.choices)
    is_primary = models.BooleanField(default=False)
    receives_communication = models.BooleanField(default=True)
    authorized_pickup = models.BooleanField(default=False)

    objects = TenantManager()

    class Meta:
        ordering = ["-is_primary", "guardian__last_name"]
        constraints = [
            models.UniqueConstraint(
                fields=["school", "learner", "guardian"],
                name="unique_learner_guardian_link",
            ),
            models.UniqueConstraint(
                fields=["school", "learner"],
                condition=Q(is_primary=True),
                name="one_primary_guardian_per_learner",
            ),
        ]
        indexes = [
            models.Index(fields=["school", "learner", "is_primary"]),
            models.Index(fields=["school", "guardian"]),
        ]

    def clean(self):
        super().clean()
        if (
            self.learner_id
            and self.guardian_id
            and (
                self.school_id != self.learner.school_id
                or self.school_id != self.guardian.school_id
            )
        ):
            raise ValidationError(
                {"guardian": "Learner and guardian must belong to the same school."}
            )

    def __str__(self):
        return f"{self.learner} - {self.guardian}"


class MedicalRecord(UUIDModel, TimeStampedModel):
    school = models.ForeignKey(
        "tenancy.School",
        on_delete=models.CASCADE,
        related_name="medical_records",
    )
    learner = models.OneToOneField(
        Learner,
        on_delete=models.PROTECT,
        related_name="medical_record",
    )
    blood_group = models.CharField(max_length=8, blank=True)
    allergies = models.TextField(blank=True)
    conditions = models.TextField(blank=True)
    medication = models.TextField(blank=True)
    emergency_notes = models.TextField(blank=True)

    objects = TenantManager()

    class Meta:
        indexes = [
            models.Index(fields=["school", "learner"]),
        ]

    def clean(self):
        super().clean()
        if self.learner_id and self.school_id != self.learner.school_id:
            raise ValidationError({"learner": "Learner must belong to the same school."})

    def __str__(self):
        return f"Medical summary for {self.learner}"


class AdmissionApplication(UUIDModel, TimeStampedModel):
    class Status(models.TextChoices):
        SUBMITTED = "submitted", "Submitted"
        REVIEWING = "reviewing", "Reviewing"
        ADMITTED = "admitted", "Admitted"
        DECLINED = "declined", "Declined"
        WITHDRAWN = "withdrawn", "Withdrawn"

    school = models.ForeignKey(
        "tenancy.School",
        on_delete=models.CASCADE,
        related_name="admission_applications",
    )
    first_name = models.CharField(max_length=80)
    middle_name = models.CharField(max_length=80, blank=True)
    last_name = models.CharField(max_length=80)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=16, choices=Learner.Gender.choices)
    desired_grade = models.ForeignKey(
        "academics.Grade",
        on_delete=models.PROTECT,
        related_name="admission_applications",
    )
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.SUBMITTED,
    )
    submitted_at = models.DateField()
    admitted_at = models.DateTimeField(null=True, blank=True)

    objects = TenantManager()

    class Meta:
        ordering = ["-submitted_at", "last_name", "first_name"]
        indexes = [
            models.Index(fields=["school", "status", "submitted_at"]),
        ]

    def clean(self):
        super().clean()
        if self.desired_grade_id and self.school_id != self.desired_grade.school_id:
            raise ValidationError({"desired_grade": "Grade must belong to the same school."})

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class AdmissionSequence(UUIDModel, TimeStampedModel):
    school = models.ForeignKey(
        "tenancy.School",
        on_delete=models.CASCADE,
        related_name="admission_sequences",
    )
    year = models.PositiveSmallIntegerField()
    last_number = models.PositiveIntegerField(default=0)

    objects = TenantManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["school", "year"],
                name="unique_admission_sequence_per_school_year",
            )
        ]

    def __str__(self):
        return f"{self.school} {self.year}: {self.last_number}"


class Enrollment(UUIDModel, TimeStampedModel):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"
        TRANSFERRED = "transferred", "Transferred"
        WITHDRAWN = "withdrawn", "Withdrawn"

    school = models.ForeignKey(
        "tenancy.School",
        on_delete=models.CASCADE,
        related_name="enrollments",
    )
    learner = models.ForeignKey(
        Learner,
        on_delete=models.PROTECT,
        related_name="enrollments",
    )
    academic_year = models.ForeignKey(
        "academics.AcademicYear",
        on_delete=models.PROTECT,
        related_name="enrollments",
    )
    grade = models.ForeignKey(
        "academics.Grade",
        on_delete=models.PROTECT,
        related_name="enrollments",
    )
    stream = models.ForeignKey(
        "academics.Stream",
        on_delete=models.PROTECT,
        related_name="enrollments",
    )
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    objects = TenantManager()

    class Meta:
        ordering = ["-start_date"]
        constraints = [
            models.UniqueConstraint(
                fields=["school", "learner"],
                condition=Q(status="active"),
                name="one_active_enrollment_per_learner",
            )
        ]
        indexes = [
            models.Index(fields=["school", "academic_year", "grade", "stream"]),
            models.Index(fields=["school", "status", "start_date"]),
        ]

    def clean(self):
        super().clean()
        errors = {}
        for field_name in ("learner", "academic_year", "grade", "stream"):
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
        return f"{self.learner} - {self.academic_year}"


class TransferRecord(UUIDModel, TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    school = models.ForeignKey(
        "tenancy.School",
        on_delete=models.CASCADE,
        related_name="transfer_records",
    )
    learner = models.ForeignKey(
        Learner,
        on_delete=models.PROTECT,
        related_name="transfer_records",
    )
    enrollment = models.ForeignKey(
        Enrollment,
        on_delete=models.PROTECT,
        related_name="transfer_records",
    )
    destination_school_name = models.CharField(max_length=200)
    transfer_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    export_reference = models.CharField(max_length=80, blank=True)
    exported_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    objects = TenantManager()

    class Meta:
        ordering = ["-transfer_date", "-created_at"]
        indexes = [
            models.Index(fields=["school", "status", "transfer_date"]),
            models.Index(fields=["school", "learner"]),
        ]

    def clean(self):
        super().clean()
        errors = {}
        if self.learner_id and self.school_id != self.learner.school_id:
            errors["learner"] = "Learner must belong to the same school."
        enrollment = self.enrollment
        if (
            self.enrollment_id
            and enrollment is not None
            and (
                self.school_id != enrollment.school_id
                or self.learner_id != enrollment.learner_id
            )
        ):
            errors["enrollment"] = "Enrollment must belong to the same learner and school."
        if (
            self.enrollment_id
            and enrollment is not None
            and self.transfer_date
            and self.transfer_date < enrollment.start_date
        ):
            errors["transfer_date"] = "Transfer date cannot precede enrollment."
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.learner} to {self.destination_school_name}"
