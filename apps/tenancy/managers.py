from django.db import models

from .exceptions import SchoolContextRequired


class TenantQuerySet(models.QuerySet):
    def for_school(self, school):
        if school is None:
            raise SchoolContextRequired("school is required")
        return self.filter(school=school)


class TenantManager(models.Manager.from_queryset(TenantQuerySet)):  # type: ignore[misc]
    pass
