from django.contrib import admin

from apps.tenancy.models import School, SchoolDomain


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active", "timezone")
    list_filter = ("is_active", "timezone")
    search_fields = ("name", "slug")


@admin.register(SchoolDomain)
class SchoolDomainAdmin(admin.ModelAdmin):
    list_display = ("hostname", "school", "is_primary")
    list_filter = ("is_primary",)
    search_fields = ("hostname", "school__name")
