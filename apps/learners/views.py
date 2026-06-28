from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import F, FilteredRelation, Q, Value
from django.db.models.functions import Coalesce
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.academics.models import Grade, Stream
from apps.accounts.decorators import school_roles_required
from apps.learners.forms import AdmissionForm, TransferForm
from apps.learners.models import AdmissionApplication, Enrollment, Learner, MedicalRecord
from apps.learners.permissions import access_medical_record, can_view_medical_record
from apps.learners.services.admissions import admit_learner
from apps.learners.services.bulk_admissions import (
    SESSION_KEY,
    build_xlsx_template,
    deserialize_session_rows,
    import_bulk_admission_rows,
    parse_bulk_admission_upload,
    serialize_cleaned_row,
)
from apps.learners.services.transfers import transfer_learner

LEARNER_VIEW_ROLES = (
    "school_admin",
    "principal",
    "deputy_principal",
    "teacher",
    "class_teacher",
    "department_head",
    "guidance_counsellor",
)
LEARNER_ADMIN_ROLES = ("school_admin", "principal", "deputy_principal")


@login_required
@school_roles_required(*LEARNER_VIEW_ROLES)
def index(request):
    learners = (
        Learner.objects.for_school(request.school)
        .annotate(
            active_enrollment=FilteredRelation(
                "enrollments",
                condition=Q(enrollments__status=Enrollment.Status.ACTIVE),
            )
        )
        .annotate(
            current_grade_id=F("active_enrollment__grade_id"),
            current_grade_name=F("active_enrollment__grade__name"),
            current_grade_order=F("active_enrollment__grade__order"),
            current_grade_order_sort=Coalesce("active_enrollment__grade__order", Value(9999)),
            current_stream_id=F("active_enrollment__stream_id"),
            current_stream_name=F("active_enrollment__stream__name"),
        )
    )
    query = request.GET.get("q", "").strip()
    selected_grade = request.GET.get("grade", "").strip()
    selected_stream = request.GET.get("stream", "").strip()
    selected_status = request.GET.get("status", "").strip()
    current_sort = request.GET.get("sort", "").strip() or "placement"
    current_direction = request.GET.get("direction", "").strip()
    if current_direction not in {"asc", "desc"}:
        current_direction = "asc"

    if query:
        learners = learners.filter(
            Q(admission_number__icontains=query)
            | Q(first_name__icontains=query)
            | Q(middle_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(active_enrollment__grade__name__icontains=query)
            | Q(active_enrollment__stream__name__icontains=query)
        )
    if selected_grade:
        learners = learners.filter(active_enrollment__grade_id=selected_grade)
    if selected_stream:
        learners = learners.filter(active_enrollment__stream_id=selected_stream)
    if selected_status:
        learners = learners.filter(status=selected_status)

    sort_options = {
        "admission": ["admission_number"],
        "name": ["first_name", "middle_name", "last_name", "admission_number"],
        "grade": ["current_grade_order_sort", "current_grade_name", "current_stream_name", "first_name", "middle_name", "last_name"],
        "stream": ["current_stream_name", "current_grade_order_sort", "first_name", "middle_name", "last_name"],
        "status": ["status", "current_grade_order_sort", "current_stream_name", "first_name", "middle_name", "last_name"],
        "placement": ["current_grade_order_sort", "current_grade_name", "current_stream_name", "first_name", "middle_name", "last_name"],
    }
    ordering = sort_options.get(current_sort, sort_options["placement"])
    if current_direction == "desc":
        ordering = [f"-{field}" for field in ordering]
    learners = learners.order_by(*ordering, "admission_number")

    grades = Grade.objects.for_school(request.school).filter(is_active=True)
    streams = Stream.objects.for_school(request.school).filter(is_active=True)
    if selected_grade:
        streams = streams.filter(grade_id=selected_grade)

    def sort_url(sort_key):
        params = request.GET.copy()
        params["sort"] = sort_key
        params["direction"] = (
            "desc" if current_sort == sort_key and current_direction == "asc" else "asc"
        )
        return f"?{params.urlencode()}"

    sort_links = {
        key: {
            "url": sort_url(key),
            "active": current_sort == key,
            "direction": current_direction if current_sort == key else "",
        }
        for key in ("admission", "name", "grade", "stream", "status")
    }

    template = (
        "learners/partials/learner_table.html"
        if request.htmx
        else "learners/index.html"
    )
    return render(
        request,
        template,
        {
            "learners": learners,
            "grades": grades,
            "streams": streams,
            "statuses": Learner.Status.choices,
            "filters": {
                "q": query,
                "grade": selected_grade,
                "stream": selected_stream,
                "status": selected_status,
                "sort": current_sort,
                "direction": current_direction,
            },
            "sort_links": sort_links,
        },
    )


@login_required
@school_roles_required(*LEARNER_VIEW_ROLES)
def detail(request, learner_id):
    learner = get_object_or_404(
        Learner.objects.for_school(request.school).prefetch_related(
            "guardian_links__guardian",
            "enrollments__academic_year",
            "enrollments__grade",
            "enrollments__stream",
            "transfer_records",
        ),
        pk=learner_id,
    )
    medical_record = None
    if (
        MedicalRecord.objects.for_school(request.school).filter(learner=learner).exists()
        and can_view_medical_record(request.user, request.school, learner)
    ):
        medical_record = access_medical_record(request.user, request.school, learner)
    return render(
        request,
        "learners/detail.html",
        {"learner": learner, "medical_record": medical_record},
    )


@login_required
@school_roles_required(*LEARNER_ADMIN_ROLES)
@transaction.atomic
def admit(request):
    form = AdmissionForm(request.POST or None, school=request.school)
    if request.method == "POST" and form.is_valid():
        application = AdmissionApplication.objects.create(
            school=request.school,
            first_name=form.cleaned_data["first_name"],
            middle_name=form.cleaned_data["middle_name"],
            last_name=form.cleaned_data["last_name"],
            date_of_birth=form.cleaned_data["date_of_birth"],
            gender=form.cleaned_data["gender"],
            desired_grade=form.cleaned_data["grade"],
            submitted_at=timezone.localdate(),
        )
        learner = admit_learner(
            school=request.school,
            actor=request.user,
            application=application,
            academic_year=form.cleaned_data["academic_year"],
            grade=form.cleaned_data["grade"],
            stream=form.cleaned_data["stream"],
            admission_date=form.cleaned_data["admission_date"],
            learner_data={},
            guardians=[
                {
                    "first_name": form.cleaned_data["guardian_first_name"],
                    "last_name": form.cleaned_data["guardian_last_name"],
                    "email": form.cleaned_data["guardian_email"],
                    "phone_number": form.cleaned_data["guardian_phone_number"],
                    "relationship": form.cleaned_data["guardian_relationship"],
                    "is_primary": True,
                }
            ],
            medical_data={
                "blood_group": form.cleaned_data["blood_group"],
                "allergies": form.cleaned_data["allergies"],
                "conditions": form.cleaned_data["conditions"],
                "medication": form.cleaned_data["medication"],
            },
        )
        messages.success(request, f"{learner.full_name} admitted successfully.")
        return redirect("learners:detail", learner_id=learner.id)
    return render(request, "learners/admit.html", {"form": form})


@login_required
@school_roles_required(*LEARNER_ADMIN_ROLES)
def bulk_admit_template(request):
    response = HttpResponse(
        build_xlsx_template(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = 'attachment; filename="learner-admission-template.xlsx"'
    return response


@login_required
@school_roles_required(*LEARNER_ADMIN_ROLES)
def bulk_admit(request):
    result = None
    if request.method == "POST":
        uploaded_file = request.FILES.get("file")
        if uploaded_file is None:
            messages.error(request, "Choose a CSV, XLSX, or XLS file to upload.")
        else:
            result = parse_bulk_admission_upload(
                uploaded_file=uploaded_file,
                school=request.school,
            )
            request.session[SESSION_KEY] = [
                serialize_cleaned_row(row.cleaned_data) for row in result.valid_rows
            ]
            request.session.modified = True
            if result.valid_count:
                messages.success(
                    request,
                    f"{result.valid_count} valid learner row(s) are ready to import.",
                )
            if result.has_errors:
                messages.error(request, "Fix the failed rows before uploading them again.")
    return render(request, "learners/bulk_admit.html", {"result": result})


@login_required
@school_roles_required(*LEARNER_ADMIN_ROLES)
def bulk_admit_confirm(request):
    if request.method != "POST":
        return redirect("learners:bulk_admit")
    serialized_rows = request.session.get(SESSION_KEY, [])
    if not serialized_rows:
        messages.error(request, "Upload and preview learner rows before confirming import.")
        return redirect("learners:bulk_admit")
    try:
        rows = deserialize_session_rows(school=request.school, rows=serialized_rows)
        learners = import_bulk_admission_rows(
            school=request.school,
            actor=request.user,
            rows=rows,
        )
    except Exception:
        messages.error(
            request,
            "The learners could not be imported. Review the file and try again.",
        )
        return redirect("learners:bulk_admit")
    request.session.pop(SESSION_KEY, None)
    request.session.modified = True
    messages.success(request, f"{len(learners)} learner(s) imported successfully.")
    return redirect("learners:index")


@login_required
@school_roles_required(*LEARNER_ADMIN_ROLES)
def transfer(request, learner_id):
    learner = get_object_or_404(
        Learner.objects.for_school(request.school),
        pk=learner_id,
    )
    form = TransferForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        transfer_learner(
            school=request.school,
            actor=request.user,
            learner=learner,
            **form.cleaned_data,
        )
        messages.success(request, f"{learner.full_name} transferred successfully.")
        return redirect("learners:detail", learner_id=learner.id)
    return render(
        request,
        "learners/transfer.html",
        {"learner": learner, "form": form},
    )
