from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.accounts.decorators import school_roles_required
from apps.activities.models import ActivityParticipation, Club


@login_required
@school_roles_required(
    "school_admin",
    "principal",
    "deputy_principal",
    "teacher",
    "class_teacher",
    "department_head",
)
def index(request):
    return render(
        request,
        "activities/index.html",
        {
            "clubs": Club.objects.for_school(request.school)[:20],
            "participation": ActivityParticipation.objects.for_school(request.school)
            .select_related("club", "learner")[:30],
        },
    )
