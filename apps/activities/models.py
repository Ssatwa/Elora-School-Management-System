from django.db import models

from apps.core.models import TimeStampedModel, UUIDModel
from apps.tenancy.managers import TenantManager


class Club(UUIDModel, TimeStampedModel):
    school = models.ForeignKey("tenancy.School", on_delete=models.CASCADE)
    name = models.CharField(max_length=160)
    category = models.CharField(max_length=80)
    patron = models.ForeignKey("accounts.Membership", on_delete=models.PROTECT)
    meeting_schedule = models.CharField(max_length=160, blank=True)
    is_active = models.BooleanField(default=True)

    objects = TenantManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["school", "name"],
                name="unique_school_club_name",
            )
        ]

    def __str__(self):
        return self.name


class ActivityParticipation(UUIDModel, TimeStampedModel):
    school = models.ForeignKey("tenancy.School", on_delete=models.CASCADE)
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name="participants")
    learner = models.ForeignKey("learners.Learner", on_delete=models.PROTECT)
    role = models.CharField(max_length=80, default="Member")
    achievements = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    objects = TenantManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["school", "club", "learner"],
                name="unique_club_participant",
            )
        ]
