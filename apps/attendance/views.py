from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_time

from apps.accounts.decorators import school_roles_required
from apps.attendance.exports import attendance_csv
from apps.attendance.forms import (
    AttendanceCorrectionForm,
    AttendanceReportForm,
    LearnerRegisterForm,
    StaffRegisterForm,
)
from apps.attendance.models import (
    AbsenceAlert,
    AttendanceRegister,
    LearnerAttendanceEntry,
    StaffAttendanceEntry,
)
from apps.attendance.services import (
    attendance_summary,
    correct_attendance,
    mark_learner_attendance,
    mark_staff_attendance,
)
from apps.learners.models import Enrollment
from apps.staff.models import TeacherProfile

ATTENDANCE_VIEW_ROLES = (
    "school_admin",
    "principal",
    "deputy_principal",
    "teacher",
    "class_teacher",
    "department_head",
    "guidance_counsellor",
)
LEARNER_ENTRY_ROLES = (
    "school_admin",
    "principal",
    "deputy_principal",
    "class_teacher",
)
CORRECTION_ROLES = ("school_admin", "principal", "deputy_principal")
STAFF_ENTRY_ROLES = CORRECTION_ROLES


def _report_dates(request):
    today = timezone.localdate()
    form = AttendanceReportForm(
        request.GET or {
            "start_date": today - timedelta(days=29),
            "end_date": today,
            "subject_type": AttendanceRegister.SubjectType.LEARNER,
        }
    )
    if form.is_valid():
        return form, form.cleaned_data
    return form, {
        "start_date": today - timedelta(days=29),
        "end_date": today,
        "subject_type": AttendanceRegister.SubjectType.LEARNER,
    }


@login_required
@school_roles_required(*ATTENDANCE_VIEW_ROLES)
def index(request):
    report_form, filters = _report_dates(request)
    registers = (
        AttendanceRegister.objects.for_school(request.school)
        .select_related("stream__grade", "marked_by")
        .order_by("-attendance_date", "session")[:20]
    )
    context = {
        "registers": registers,
        "alerts": AbsenceAlert.objects.for_school(request.school)
        .select_related("learner_entry__learner", "staff_entry__teacher")[:8],
        "summary": attendance_summary(school=request.school, **filters),
        "report_form": report_form,
    }
    template = (
        "attendance/partials/register_table.html"
        if request.htmx
        else "attendance/index.html"
    )
    return render(request, template, context)


@login_required
@school_roles_required(*LEARNER_ENTRY_ROLES)
def learner_register(request):
    form = LearnerRegisterForm(request.POST or request.GET or None, school=request.school)
    learners = []
    stream = None
    if form.is_valid():
        stream = form.cleaned_data["stream"]
        learners = list(
            Enrollment.objects.for_school(request.school)
            .filter(stream=stream, status=Enrollment.Status.ACTIVE)
            .select_related("learner")
            .order_by("learner__last_name", "learner__first_name")
        )
    if request.method == "POST" and form.is_valid():
        rows = []
        for enrollment in learners:
            learner = enrollment.learner
            rows.append(
                {
                    "learner": learner,
                    "status": request.POST.get(
                        f"status_{learner.id}",
                        LearnerAttendanceEntry.Status.PRESENT,
                    ),
                    "note": request.POST.get(f"note_{learner.id}", ""),
                }
            )
        mark_learner_attendance(
            school=request.school,
            actor=request.user,
            attendance_date=form.cleaned_data["attendance_date"],
            session=form.cleaned_data["session"],
            stream=stream,
            rows=rows,
        )
        messages.success(request, "Learner attendance register completed.")
        return redirect("attendance:index")
    return render(
        request,
        "attendance/learner_register.html",
        {"form": form, "enrollments": learners},
    )


@login_required
@school_roles_required(*STAFF_ENTRY_ROLES)
def staff_register(request):
    form = StaffRegisterForm(request.POST or None)
    teachers = list(
        TeacherProfile.objects.for_school(request.school)
        .filter(status=TeacherProfile.Status.ACTIVE)
        .select_related("membership__user")
    )
    if request.method == "POST" and form.is_valid():
        rows = []
        for teacher in teachers:
            rows.append(
                {
                    "teacher": teacher,
                    "status": request.POST.get(
                        f"status_{teacher.id}",
                        StaffAttendanceEntry.Status.PRESENT,
                    ),
                    "arrival_time": parse_time(
                        request.POST.get(f"arrival_time_{teacher.id}", "")
                    ),
                    "note": request.POST.get(f"note_{teacher.id}", ""),
                }
            )
        mark_staff_attendance(
            school=request.school,
            actor=request.user,
            attendance_date=form.cleaned_data["attendance_date"],
            session=form.cleaned_data["session"],
            rows=rows,
        )
        messages.success(request, "Staff attendance register completed.")
        return redirect("attendance:index")
    return render(
        request,
        "attendance/staff_register.html",
        {"form": form, "teachers": teachers},
    )


@login_required
@school_roles_required(*CORRECTION_ROLES)
def correct_learner_entry(request, entry_id):
    entry = get_object_or_404(
        LearnerAttendanceEntry.objects.for_school(request.school).select_related("learner"),
        pk=entry_id,
    )
    form = AttendanceCorrectionForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        correct_attendance(
            school=request.school,
            actor=request.user,
            entry=entry,
            new_status=form.cleaned_data["status"],
            new_arrival_time=form.cleaned_data["arrival_time"],
            new_note=form.cleaned_data["note"],
            reason=form.cleaned_data["reason"],
        )
        messages.success(request, "Attendance correction recorded.")
        return redirect("attendance:index")
    return render(
        request,
        "attendance/correct.html",
        {"form": form, "entry": entry},
    )


@login_required
@school_roles_required(*CORRECTION_ROLES)
def correct_staff_entry(request, entry_id):
    entry = get_object_or_404(
        StaffAttendanceEntry.objects.for_school(request.school).select_related("teacher"),
        pk=entry_id,
    )
    form = AttendanceCorrectionForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        correct_attendance(
            school=request.school,
            actor=request.user,
            entry=entry,
            new_status=form.cleaned_data["status"],
            new_arrival_time=form.cleaned_data["arrival_time"],
            new_note=form.cleaned_data["note"],
            reason=form.cleaned_data["reason"],
        )
        messages.success(request, "Attendance correction recorded.")
        return redirect("attendance:index")
    return render(
        request,
        "attendance/correct.html",
        {"form": form, "entry": entry},
    )


@login_required
@school_roles_required(*ATTENDANCE_VIEW_ROLES)
def export(request):
    report_form, filters = _report_dates(request)
    content = attendance_csv(
        school=request.school,
        start_date=filters["start_date"],
        end_date=filters["end_date"],
    )
    response = HttpResponse(content, content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="attendance.csv"'
    return response
