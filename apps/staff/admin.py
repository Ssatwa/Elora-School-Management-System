from django.contrib import admin

from apps.staff.models import Department, StaffAssignment, TeacherProfile


@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ("employee_number", "membership", "school", "status")
    list_filter = ("school", "status")
    search_fields = ("employee_number", "membership__user__email")


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "school", "head", "is_active")
    list_filter = ("school", "is_active")
    search_fields = ("name", "code")


@admin.register(StaffAssignment)
class StaffAssignmentAdmin(admin.ModelAdmin):
    list_display = ("teacher", "role", "school", "start_date", "end_date")
    list_filter = ("school", "role")
    search_fields = ("teacher__employee_number",)
