from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.accounts.decorators import school_roles_required
from apps.wellbeing.models import DisciplineRecord


@login_required
@school_roles_required(
    "school_admin",
    "principal",
    "deputy_principal",
    "guidance_counsellor",
    "class_teacher",
)
def index(request):
    return render(
        request,
        "wellbeing/index.html",
        {
            "records": DisciplineRecord.objects.for_school(request.school)
            .select_related("learner", "recorded_by")[:30]
        },
    )
