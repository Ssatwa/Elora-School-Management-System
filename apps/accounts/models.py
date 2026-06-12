import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.accounts.managers import UserManager
from apps.core.models import TimeStampedModel, UUIDModel
from apps.tenancy.managers import TenantManager


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = None
    email = models.EmailField(unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email


class Role(UUIDModel):
    code = models.SlugField(max_length=64, unique=True)
    name = models.CharField(max_length=100)
    is_platform_role = models.BooleanField(default=False)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Membership(UUIDModel, TimeStampedModel):
    school = models.ForeignKey(
        "tenancy.School",
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    roles = models.ManyToManyField(Role, related_name="memberships")
    is_active = models.BooleanField(default=True)

    objects = TenantManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["school", "user"],
                name="unique_school_user_membership",
            )
        ]

    def __str__(self):
        return f"{self.user} at {self.school}"
