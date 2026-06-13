from django.contrib import admin

from apps.accounts.models import AuditLog, Membership, Role, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("email", "first_name", "last_name", "is_active", "is_staff")
    list_filter = ("is_active", "is_staff", "is_superuser")
    search_fields = ("email", "first_name", "last_name")


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "is_platform_role")
    list_filter = ("is_platform_role",)
    search_fields = ("name", "code")


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "school", "is_active", "created_at")
    list_filter = ("is_active", "school")
    search_fields = ("user__email", "school__name")
    filter_horizontal = ("roles",)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = (
        "created_at",
        "action",
        "target_type",
        "target_id",
        "school",
        "actor",
    )
    list_filter = ("action", "target_type", "school")
    search_fields = ("target_id", "request_id", "actor__email")
    readonly_fields = (
        "school",
        "actor",
        "action",
        "target_type",
        "target_id",
        "request_id",
        "metadata",
        "created_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
