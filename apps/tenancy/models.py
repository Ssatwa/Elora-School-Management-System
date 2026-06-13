from django.db import models

from apps.core.models import TimeStampedModel, UUIDModel


class School(UUIDModel, TimeStampedModel):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=80, unique=True)
    is_active = models.BooleanField(default=True)
    primary_color = models.CharField(max_length=7, default="#1D4ED8")
    secondary_color = models.CharField(max_length=7, default="#0F766E")
    timezone = models.CharField(max_length=64, default="Africa/Nairobi")

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class SchoolDomain(UUIDModel, TimeStampedModel):
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="domains",
    )
    hostname = models.CharField(max_length=253, unique=True)
    is_primary = models.BooleanField(default=False)

    class Meta:
        ordering = ["hostname"]

    def __str__(self):
        return self.hostname
