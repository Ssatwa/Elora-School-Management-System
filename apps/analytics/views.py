from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import HttpResponseForbidden
from django.shortcuts import render
from django.utils import timezone

from apps.academics.models import Term
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


def _dashboard_shortcuts(role_code):
    shortcuts = {
        "school_admin": [
            {
                "label": "Manage academic structure",
                "description": "Grades, streams and learning areas",
                "url": "/academics/",
            },
            {
                "label": "Manage staff",
                "description": "Assignments and workloads",
                "url": "/staff/",
            },
            {
                "label": "Admit learner",
                "description": "Create a new learner record",
                "url": "/learners/admit/",
            },
        ],
        "principal": [
            {
                "label": "Review report cards",
                "description": "Approve learner reports",
                "url": "/reports/",
            },
            {
                "label": "View attendance",
                "description": "Monitor daily participation",
                "url": "/attendance/",
            },
        ],
        "teacher": [
            {
                "label": "Open assessments",
                "description": "Record CBC evidence",
                "url": "/assessments/",
            },
            {
                "label": "View timetable",
                "description": "Review today's lessons",
                "url": "/timetables/",
            },
        ],
        "class_teacher": [
            {
                "label": "Take attendance",
                "description": "Complete the learner register",
                "url": "/attendance/learners/",
            },
            {
                "label": "Open assessments",
                "description": "Record CBC evidence",
                "url": "/assessments/",
            },
        ],
        "accountant": [
            {
                "label": "Open finance",
                "description": "Invoices, receipts and balances",
                "url": "/finance/",
            }
        ],
        "librarian": [
            {
                "label": "Open library",
                "description": "Loans, returns and overdue books",
                "url": "/library/",
            }
        ],
        "guidance_counsellor": [
            {
                "label": "Open wellbeing",
                "description": "Review learner support records",
                "url": "/wellbeing/",
            }
        ],
    }
    return shortcuts.get(role_code, [])


def _dashboard_data(user, school, role_code):
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
    absent = attendance.filter(status=LearnerAttendanceEntry.Status.ABSENT).count()
    late = attendance.filter(status=LearnerAttendanceEntry.Status.LATE).count()
    excused = attendance.filter(status=LearnerAttendanceEntry.Status.EXCUSED).count()
    attendance_rate = round((present / attendance.count()) * 100) if attendance.exists() else 0
    published_reports = ReportCard.objects.for_school(school).filter(
        learner_id__in=learner_ids,
        status=ReportCard.Status.PUBLISHED,
    ).count()
    metrics = [
        {
            "label": "Total learners",
            "value": learners.count(),
            "tone": "primary",
            "trend": "Active learner records",
        },
        {
            "label": "Attendance rate",
            "value": f"{attendance_rate}%",
            "tone": "success" if attendance_rate >= 80 else "warning",
            "trend": f"{present} present entries",
        },
        {
            "label": "Published reports",
            "value": published_reports,
            "tone": "primary",
            "trend": "Available to families",
        },
        {
            "label": "Fee collection",
            "value": f"KES {paid:,.0f}",
            "tone": "success",
            "trend": "Confirmed payments",
        },
    ]
    performance_chart = {
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
    attendance_chart = {
        "labels": ["Present", "Absent", "Late", "Excused"],
        "values": [present, absent, late, excused],
    }
    today = timezone.localdate()
    current_term = (
        Term.objects.for_school(school)
        .filter(start_date__lte=today, end_date__gte=today)
        .select_related("academic_year")
        .first()
    )
    announcements = list(Announcement.objects.for_school(school)[:5])
    upcoming_events = []
    if current_term:
        upcoming_events.append(
            {
                "date": current_term.end_date,
                "title": f"{current_term.name} closes",
                "category": current_term.academic_year.name,
            }
        )
    upcoming_events.extend(
        {
            "date": item.published_at.date(),
            "title": item.title,
            "category": "Announcement",
        }
        for item in announcements[:3]
    )
    fee_activity = list(
        payments.select_related("learner").order_by("-paid_on", "-created_at")[:5]
    )
    recent_reports = list(
        ReportCard.objects.for_school(school)
        .filter(learner_id__in=learner_ids)
        .select_related("learner", "term")[:3]
    )
    recent_activity = [
        {
            "title": item.title,
            "meta": f"Announcement · {item.published_at:%b %d}",
        }
        for item in announcements[:3]
    ]
    recent_activity.extend(
        {
            "title": f"Report card · {item.learner.full_name}",
            "meta": f"{item.term.name} · {item.get_status_display()}",
        }
        for item in recent_reports
    )
    return {
        "metrics": metrics,
        "performance_chart": performance_chart,
        "performance_rows": zip(
            performance_chart["labels"],
            performance_chart["values"],
            strict=True,
        ),
        "attendance_chart": attendance_chart,
        "attendance_rows": zip(
            attendance_chart["labels"],
            attendance_chart["values"],
            strict=True,
        ),
        "outstanding_fees": invoiced - paid,
        "announcements": announcements,
        "upcoming_events": upcoming_events[:4],
        "fee_activity": fee_activity,
        "recent_activity": recent_activity[:5],
        "shortcuts": _dashboard_shortcuts(role_code),
        "current_term": current_term,
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
    role_code = role.code if role else ""
    live_data = _dashboard_data(request.user, request.school, role_code)
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
