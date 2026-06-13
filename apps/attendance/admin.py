from django.contrib import admin

from apps.attendance.models import (
    AbsenceAlert,
    AttendanceCorrection,
    AttendanceRegister,
    LearnerAttendanceEntry,
    StaffAttendanceEntry,
)

admin.site.register(AttendanceRegister)
admin.site.register(LearnerAttendanceEntry)
admin.site.register(StaffAttendanceEntry)
admin.site.register(AttendanceCorrection)
admin.site.register(AbsenceAlert)
