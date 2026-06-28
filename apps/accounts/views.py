from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View

from apps.accounts.forms import SchoolAuthenticationForm
from apps.accounts.models import Membership


class SchoolLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = SchoolAuthenticationForm
    redirect_authenticated_user = True

    def dispatch(self, request, *args, **kwargs):
        host = request.get_host().split(":", 1)[0].lower()
        if getattr(request, "school", None) and host not in {
            "localhost",
            "127.0.0.1",
            "testserver",
        }:
            return redirect(universal_login_url(request))
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        memberships = _active_memberships(self.request.user)
        if len(memberships) == 1:
            self.request.session["active_school_id"] = str(memberships[0].school_id)
            return reverse("analytics:dashboard")
        return reverse("accounts:select_school")


def universal_logout(request):
    logout(request)
    request.session.pop("active_school_id", None)
    return redirect(universal_login_url(request))


@method_decorator(login_required, name="dispatch")
class SchoolSelectionView(View):
    template_name = "accounts/select_school.html"

    def get(self, request):
        memberships = _active_memberships(request.user)
        return render(
            request,
            self.template_name,
            {
                "memberships": memberships,
            },
        )

    def post(self, request):
        school_id = request.POST.get("school")
        membership = (
            Membership.objects.select_related("school")
            .filter(user=request.user, school_id=school_id, is_active=True)
            .first()
        )
        if membership is None:
            raise PermissionDenied("You do not have access to that school.")
        request.session["active_school_id"] = str(membership.school_id)
        return redirect("analytics:dashboard")


def _active_memberships(user):
    return list(
        Membership.objects.select_related("school")
        .prefetch_related("roles")
        .filter(user=user, is_active=True, school__is_active=True)
        .order_by("school__name")
    )


def school_dashboard_url(request, school):
    domain = school.domains.order_by("-is_primary", "hostname").first()
    if domain is None:
        return reverse("analytics:dashboard")

    host = domain.hostname
    current_host = request.get_host()
    port = current_host.rsplit(":", 1)[1] if ":" in current_host else request.get_port()
    if port not in {"80", "443"}:
        host = f"{host}:{port}"
    return f"{request.scheme}://{host}{reverse('analytics:dashboard')}"


def universal_login_url(request):
    host = "localhost"
    current_host = request.get_host()
    port = current_host.rsplit(":", 1)[1] if ":" in current_host else request.get_port()
    if port not in {"80", "443"}:
        host = f"{host}:{port}"
    return f"{request.scheme}://{host}{reverse('accounts:login')}"
