from django.db import models

from apps.core.models import TimeStampedModel, UUIDModel
from apps.tenancy.managers import TenantManager


class Announcement(UUIDModel, TimeStampedModel):
    school = models.ForeignKey("tenancy.School", on_delete=models.CASCADE)
    title = models.CharField(max_length=180)
    body = models.TextField()
    published_by = models.ForeignKey("accounts.User", on_delete=models.PROTECT)
    published_at = models.DateTimeField()

    objects = TenantManager()

    class Meta:
        ordering = ["-published_at"]

    def __str__(self):
        return self.title


class Notification(UUIDModel, TimeStampedModel):
    school = models.ForeignKey("tenancy.School", on_delete=models.CASCADE)
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE)
    announcement = models.ForeignKey(
        Announcement,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=180)
    body = models.TextField()
    read_at = models.DateTimeField(null=True, blank=True)
    delivery_status = models.CharField(max_length=20, default="queued")

    objects = TenantManager()

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["school", "user", "read_at"])]


class Message(UUIDModel, TimeStampedModel):
    school = models.ForeignKey("tenancy.School", on_delete=models.CASCADE)
    sender = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        related_name="sent_school_messages",
    )
    recipient = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        related_name="received_school_messages",
    )
    subject = models.CharField(max_length=180)
    body = models.TextField()
    read_at = models.DateTimeField(null=True, blank=True)

    objects = TenantManager()

    class Meta:
        ordering = ["-created_at"]
