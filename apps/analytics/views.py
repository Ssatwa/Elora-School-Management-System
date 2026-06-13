from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import HttpResponseForbidden
from django.shortcuts import render

from apps.accounts.models import Membership
from apps.accounts.permissions import has_school_role
from apps.analytics.dashboard_registry import DASHBOARDS
from apps.assessments.models import AssessmentResult
from apps.attendance.models import LearnerAttendanceEntry
from apps.communication.models import Announcement
from apps.finance.models import Invoice, Payment
from apps.learners.models import Learner
from apps.library.models import BorrowRecord
from apps.reports.models import ReportCard


def _visible_learners(user, school):
    learners = Learner.objects.for_school(school)
    if has_school_role(user, school, "parent"):
        return learners.filter(
            guardian_links__guardian__membership__user=user
        ).distinct()
    if has_school_role(user, school, "learner"):
        return learners.filter(membership__user=user)
    return learners


def _dashboard_data(user, school):
    learners = _visible_learners(user, school)
    learner_ids = learners.values_list("id", flat=True)
    invoices = Invoice.objects.for_school(school).filter(learner_id__in=learner_ids)
    payments = Payment.objects.for_school(school).filter(
        learner_id__in=learner_ids,
        reversed_at__isnull=True,
    )
    invoiced = invoices.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    paid = payments.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    attendance = LearnerAttendanceEntry.objects.for_school(school).filter(
        learner_id__in=learner_ids
    )
    present = attendance.filter(status=LearnerAttendanceEntry.Status.PRESENT).count()
    attendance_rate = round((present / attendance.count()) * 100) if attendance.exists() else 0
    published_reports = ReportCard.objects.for_school(school).filter(
        learner_id__in=learner_ids,
        status=ReportCard.Status.PUBLISHED,
    ).count()
    metrics = [
        {"label": "Total learners", "value": learners.count()},
        {"label": "Attendance rate", "value": f"{attendance_rate}%"},
        {"label": "Published reports", "value": published_reports},
        {"label": "Fee collection", "value": f"KES {paid:,.0f}"},
    ]
    chart = {
        "labels": ["Learners", "Assessments", "Reports", "Active loans"],
        "values": [
            learners.count(),
            AssessmentResult.objects.for_school(school)
            .filter(learner_id__in=learner_ids, is_complete=True)
            .count(),
            published_reports,
            BorrowRecord.objects.for_school(school)
            .filter(
                learner_id__in=learner_ids,
                status=BorrowRecord.Status.BORROWED,
            )
            .count(),
        ],
    }
    return {
        "metrics": metrics,
        "chart": chart,
        "chart_rows": zip(chart["labels"], chart["values"], strict=True),
        "outstanding_fees": invoiced - paid,
        "announcements": Announcement.objects.for_school(school)[:5],
    }


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
    live_data = _dashboard_data(request.user, request.school)
    dashboard_config = {**dashboard_config, "metrics": live_data["metrics"]}
    return render(
        request,
        "analytics/dashboard.html",
        {
            "membership": membership,
            "active_role": role,
            "dashboard": dashboard_config,
            **live_data,
        },
    )
