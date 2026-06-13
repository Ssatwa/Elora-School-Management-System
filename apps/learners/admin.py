from django.contrib import admin

from apps.learners.models import (
    AdmissionApplication,
    AdmissionSequence,
    Enrollment,
    Guardian,
    Learner,
    LearnerGuardian,
    MedicalRecord,
    TransferRecord,
)


@admin.register(Learner)
class LearnerAdmin(admin.ModelAdmin):
    list_display = ("admission_number", "full_name", "school", "status")
    list_filter = ("school", "status", "gender")
    search_fields = ("admission_number", "first_name", "middle_name", "last_name")


@admin.register(Guardian)
class GuardianAdmin(admin.ModelAdmin):
    list_display = ("full_name", "school", "email", "phone_number")
    list_filter = ("school",)
    search_fields = ("first_name", "last_name", "email", "phone_number")


@admin.register(
    LearnerGuardian,
    MedicalRecord,
    AdmissionApplication,
    AdmissionSequence,
    Enrollment,
    TransferRecord,
)
class LearnerOperationsAdmin(admin.ModelAdmin):
    list_filter = ("school",)
