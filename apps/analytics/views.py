from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import render

from apps.accounts.models import Membership
from apps.analytics.dashboard_registry import DASHBOARDS


@login_required
def dashboard(request):
    membership = (
        Membership.objects.select_related("school")
        .prefetch_related("roles")
        .filter(user=request.user, school=request.school, is_active=True)
        .first()
    )
    if membership is None:
        return HttpResponseForbidden("You do not have access to this school.")

    role = membership.roles.order_by("name").first()
    dashboard_config = DASHBOARDS.get(
        role.code if role else "",
        {"heading": "Dashboard", "metrics": []},
    )
    return render(
        request,
        "analytics/dashboard.html",
        {
            "membership": membership,
            "active_role": role,
            "dashboard": dashboard_config,
        },
    )
