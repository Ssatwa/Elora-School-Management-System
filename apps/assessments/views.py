from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.decorators import school_roles_required
from apps.assessments.models import Assessment, AssessmentResult
from apps.assessments.services import approve_assessment, moderate_assessment

ASSESSMENT_VIEW_ROLES = (
    "school_admin",
    "principal",
    "deputy_principal",
    "teacher",
    "class_teacher",
    "department_head",
)


@login_required
@school_roles_required(*ASSESSMENT_VIEW_ROLES)
def index(request):
    assessments = Assessment.objects.for_school(request.school).select_related(
        "stream__grade",
        "learning_area",
        "teacher__membership__user",
    )
    summary = {
        "total": assessments.count(),
        "awaiting_moderation": assessments.filter(
            status=Assessment.Status.SUBMITTED
        ).count(),
        "awaiting_approval": assessments.filter(
            status=Assessment.Status.MODERATED
        ).count(),
        "completed_results": AssessmentResult.objects.for_school(request.school)
        .filter(is_complete=True)
        .count(),
    }
    return render(
        request,
        "assessments/index.html",
        {"assessments": assessments[:30], "summary": summary},
    )


@login_required
@school_roles_required(
    "school_admin",
    "principal",
    "deputy_principal",
    "department_head",
)
def moderate(request, assessment_id):
    assessment = get_object_or_404(
        Assessment.objects.for_school(request.school),
        pk=assessment_id,
    )
    if request.method == "POST":
        moderate_assessment(
            school=request.school,
            actor=request.user,
            assessment=assessment,
            comment=request.POST.get("comment", ""),
        )
        messages.success(request, "Assessment moderated and sent for approval.")
    return redirect("assessments:index")


@login_required
@school_roles_required("school_admin", "principal")
def approve(request, assessment_id):
    assessment = get_object_or_404(
        Assessment.objects.for_school(request.school),
        pk=assessment_id,
    )
    if request.method == "POST":
        approve_assessment(
            school=request.school,
            actor=request.user,
            assessment=assessment,
            comment=request.POST.get("comment", ""),
        )
        messages.success(request, "Assessment approved for reporting.")
    return redirect("assessments:index")
