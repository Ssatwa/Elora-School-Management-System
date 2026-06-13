from django.db import models

from apps.core.models import TimeStampedModel, UUIDModel
from apps.tenancy.managers import TenantManager


class DisciplineRecord(UUIDModel, TimeStampedModel):
    class Category(models.TextChoices):
        POSITIVE = "positive", "Positive conduct"
        CONCERN = "concern", "Behaviour concern"
        COUNSELLING = "counselling", "Counselling"

    school = models.ForeignKey("tenancy.School", on_delete=models.CASCADE)
    learner = models.ForeignKey("learners.Learner", on_delete=models.PROTECT)
    category = models.CharField(max_length=16, choices=Category.choices)
    title = models.CharField(max_length=180)
    details = models.TextField()
    action_taken = models.TextField(blank=True)
    is_confidential = models.BooleanField(default=False)
    recorded_by = models.ForeignKey("accounts.User", on_delete=models.PROTECT)

    objects = TenantManager()

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["school", "learner", "category"])]

    def __str__(self):
        return self.title
