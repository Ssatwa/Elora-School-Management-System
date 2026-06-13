import csv
from io import StringIO

from apps.attendance.models import LearnerAttendanceEntry, StaffAttendanceEntry


def attendance_csv(*, school, start_date, end_date):
    output = StringIO()
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(
        [
            "attendance_date",
            "session",
            "subject_type",
            "identifier",
            "name",
            "status",
            "arrival_time",
            "note",
        ]
    )
    learners = (
        LearnerAttendanceEntry.objects.for_school(school)
        .filter(register__attendance_date__range=(start_date, end_date))
        .select_related("register", "learner")
        .order_by("register__attendance_date", "learner__admission_number")
    )
    for entry in learners:
        writer.writerow(
            [
                entry.register.attendance_date,
                entry.register.session,
                entry.register.subject_type,
                entry.learner.admission_number,
                entry.learner.full_name,
                entry.status,
                entry.arrival_time or "",
                entry.note,
            ]
        )
    staff = (
        StaffAttendanceEntry.objects.for_school(school)
        .filter(register__attendance_date__range=(start_date, end_date))
        .select_related("register", "teacher__membership__user")
        .order_by("register__attendance_date", "teacher__employee_number")
    )
    for entry in staff:
        writer.writerow(
            [
                entry.register.attendance_date,
                entry.register.session,
                entry.register.subject_type,
                entry.teacher.employee_number,
                entry.teacher.membership.user.get_full_name()
                or entry.teacher.membership.user.email,
                entry.status,
                entry.arrival_time or "",
                entry.note,
            ]
        )
    return output.getvalue()
