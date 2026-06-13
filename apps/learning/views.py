from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.accounts.decorators import school_roles_required
from apps.accounts.permissions import has_school_role
from apps.learning.models import Assignment, Resource

LEARNING_ROLES = (
    "school_admin",
    "principal",
    "deputy_principal",
    "teacher",
    "class_teacher",
    "department_head",
    "learner",
    "parent",
)


@login_required
@school_roles_required(*LEARNING_ROLES)
def index(request):
    assignments = Assignment.objects.for_school(request.school).select_related(
        "stream__grade", "learning_area", "teacher"
    )
    if has_school_role(request.user, request.school, "learner"):
        assignments = assignments.filter(
            stream__enrollments__learner__membership__user=request.user
        )
    return render(
        request,
        "learning/index.html",
        {
            "assignments": assignments.distinct()[:20],
            "resources": Resource.objects.for_school(request.school).filter(
                is_published=True
            )[:12],
        },
    )
