from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import TimeStampedModel, UUIDModel
from apps.tenancy.managers import TenantManager


class ReportCard(UUIDModel, TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending generation"
        GENERATING = "generating", "Generating"
        READY = "ready", "Ready"
        PUBLISHED = "published", "Published"
        FAILED = "failed", "Failed"

    school = models.ForeignKey(
        "tenancy.School",
        on_delete=models.CASCADE,
        related_name="report_cards",
    )
    learner = models.ForeignKey(
        "learners.Learner",
        on_delete=models.PROTECT,
        related_name="report_cards",
    )
    term = models.ForeignKey(
        "academics.Term",
        on_delete=models.PROTECT,
        related_name="report_cards",
    )
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    snapshot = models.JSONField()
    snapshot_hash = models.CharField(max_length=64)
    principal_remark = models.TextField(blank=True)
    pdf = models.FileField(upload_to="report-cards/%Y/%m/", blank=True)
    pdf_checksum = models.CharField(max_length=64, blank=True)
    generated_at = models.DateTimeField(null=True, blank=True)
    published_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="published_report_cards",
    )
    published_at = models.DateTimeField(null=True, blank=True)

    objects = TenantManager()

    class Meta:
        ordering = ["-term__start_date", "learner__last_name"]
        constraints = [
            models.UniqueConstraint(
                fields=["school", "learner", "term"],
                name="unique_report_card_per_learner_term",
            )
        ]
        indexes = [
            models.Index(fields=["school", "status", "term"]),
            models.Index(fields=["school", "learner"]),
        ]

    def clean(self):
        super().clean()
        errors = {}
        if self.learner_id and self.learner.school_id != self.school_id:
            errors["learner"] = "Learner must belong to the same school."
        if self.term_id and self.term.school_id != self.school_id:
            errors["term"] = "Term must belong to the same school."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        if self.pk:
            stored = type(self).objects.filter(pk=self.pk).values(
                "snapshot",
                "snapshot_hash",
                "learner_id",
                "term_id",
                "principal_remark",
            ).first()
            if stored and any(
                (
                    stored["snapshot"] != self.snapshot,
                    stored["snapshot_hash"] != self.snapshot_hash,
                    stored["learner_id"] != self.learner_id,
                    stored["term_id"] != self.term_id,
                    stored["principal_remark"] != self.principal_remark,
                )
            ):
                raise ValidationError("Published report snapshot data is immutable.")
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.learner} - {self.term}"


class ReportGenerationJob(UUIDModel, TimeStampedModel):
    class Status(models.TextChoices):
        QUEUED = "queued", "Queued"
        RUNNING = "running", "Running"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    school = models.ForeignKey(
        "tenancy.School",
        on_delete=models.CASCADE,
        related_name="report_generation_jobs",
    )
    report = models.OneToOneField(
        ReportCard,
        on_delete=models.CASCADE,
        related_name="generation_job",
    )
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.QUEUED)
    attempts = models.PositiveSmallIntegerField(default=0)
    last_error = models.TextField(blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    objects = TenantManager()

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["school", "status", "created_at"])]

    def clean(self):
        super().clean()
        if self.report_id and self.report.school_id != self.school_id:
            raise ValidationError({"report": "Report must belong to the same school."})

    def __str__(self):
        return f"{self.report} - {self.get_status_display()}"
