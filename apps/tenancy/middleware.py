from django.http import Http404

from apps.tenancy.context import current_school
from apps.tenancy.models import SchoolDomain
from apps.tenancy.rls import clear_database_school, set_database_school


class TenantMiddleware:
    platform_hosts = {"localhost", "127.0.0.1", "testserver"}

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().split(":", 1)[0].lower()
        request.school = None
        token = current_school.set(None)
        try:
            if host not in self.platform_hosts:
                domain = (
                    SchoolDomain.objects.select_related("school")
                    .filter(hostname=host, school__is_active=True)
                    .first()
                )
                if domain is None:
                    raise Http404("School not found")
                request.school = domain.school
                current_school.set(domain.school)
                set_database_school(domain.school.id)

            response = self.get_response(request)
            if request.school:
                response.headers["X-Elora-School"] = str(request.school.id)
            return response
        finally:
            clear_database_school()
            current_school.reset(token)
