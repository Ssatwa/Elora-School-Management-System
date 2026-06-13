from django.contrib.auth.decorators import login_required
from django.http import FileResponse
from django.shortcuts import get_object_or_404, render

from apps.accounts.decorators import school_roles_required
from apps.accounts.permissions import has_school_role
from apps.reports.models import ReportCard

REPORT_VIEW_ROLES = (
    "school_admin",
    "principal",
    "deputy_principal",
    "teacher",
    "class_teacher",
    "department_head",
    "parent",
)


def _visible_reports(request):
    reports = ReportCard.objects.for_school(request.school)
    if has_school_role(request.user, request.school, "parent"):
        reports = reports.filter(
            learner__guardian_links__guardian__membership__user=request.user
        )
    return reports


@login_required
@school_roles_required(*REPORT_VIEW_ROLES)
def index(request):
    reports = _visible_reports(request).select_related(
        "learner",
        "term",
        "published_by",
    )
    summary = {
        "total": reports.count(),
        "published": reports.filter(status=ReportCard.Status.PUBLISHED).count(),
        "ready": reports.filter(status=ReportCard.Status.READY).count(),
        "pending": reports.filter(
            status__in=(ReportCard.Status.PENDING, ReportCard.Status.GENERATING)
        ).count(),
    }
    return render(
        request,
        "reports/index.html",
        {"reports": reports[:30], "summary": summary},
    )


@login_required
@school_roles_required(*REPORT_VIEW_ROLES)
def download(request, report_id):
    report = get_object_or_404(
        _visible_reports(request),
        pk=report_id,
        status=ReportCard.Status.PUBLISHED,
    )
    report.pdf.open("rb")
    return FileResponse(
        report.pdf,
        content_type="application/pdf",
        as_attachment=True,
        filename=f"{report.learner.admission_number}-report-card.pdf",
    )
