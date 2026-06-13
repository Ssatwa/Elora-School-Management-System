from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.accounts.decorators import school_roles_required
from apps.learners.forms import AdmissionForm, TransferForm
from apps.learners.models import AdmissionApplication, Learner, MedicalRecord
from apps.learners.permissions import access_medical_record, can_view_medical_record
from apps.learners.services.admissions import admit_learner
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
    learners = Learner.objects.for_school(request.school)
    query = request.GET.get("q", "").strip()
    if query:
        learners = learners.filter(
            Q(admission_number__icontains=query)
            | Q(first_name__icontains=query)
            | Q(middle_name__icontains=query)
            | Q(last_name__icontains=query)
        )
    template = (
        "learners/partials/learner_table.html"
        if request.htmx
        else "learners/index.html"
    )
    return render(request, template, {"learners": learners})


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
