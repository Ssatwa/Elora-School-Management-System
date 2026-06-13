from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import get_object_or_404, render

from apps.accounts.decorators import school_roles_required
from apps.accounts.permissions import has_school_role
from apps.finance.models import Invoice, Payment, Receipt
from apps.learners.models import Learner

FINANCE_VIEW_ROLES = ("school_admin", "principal", "accountant", "parent", "learner")


def _visible_learners(request):
    learners = Learner.objects.for_school(request.school)
    if has_school_role(request.user, request.school, "parent"):
        return learners.filter(
            guardian_links__guardian__membership__user=request.user
        ).distinct()
    if has_school_role(request.user, request.school, "learner"):
        return learners.filter(membership__user=request.user)
    return learners


@login_required
@school_roles_required(*FINANCE_VIEW_ROLES)
def index(request):
    learners = _visible_learners(request)
    invoices = Invoice.objects.for_school(request.school).filter(learner__in=learners)
    payments = Payment.objects.for_school(request.school).filter(learner__in=learners)
    invoiced = invoices.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    paid = payments.filter(reversed_at__isnull=True).aggregate(total=Sum("amount"))[
        "total"
    ] or Decimal("0.00")
    return render(
        request,
        "finance/index.html",
        {
            "learners": learners.order_by("last_name", "first_name"),
            "invoices": invoices.select_related("learner", "term")[:20],
            "summary": {
                "invoiced": invoiced,
                "paid": paid,
                "balance": invoiced - paid,
                "open_invoices": invoices.exclude(status=Invoice.Status.PAID).count(),
            },
        },
    )


@login_required
@school_roles_required(*FINANCE_VIEW_ROLES)
def statement(request, learner_id):
    learner = get_object_or_404(_visible_learners(request), pk=learner_id)
    invoices = Invoice.objects.for_school(request.school).filter(learner=learner)
    payments = Payment.objects.for_school(request.school).filter(learner=learner)
    return render(
        request,
        "finance/statement.html",
        {"learner": learner, "invoices": invoices, "payments": payments},
    )


@login_required
@school_roles_required(*FINANCE_VIEW_ROLES)
def receipt(request, receipt_id):
    receipt = get_object_or_404(
        Receipt.objects.for_school(request.school).select_related(
            "allocation__invoice__learner",
            "allocation__payment",
            "issued_by",
        ),
        pk=receipt_id,
        allocation__invoice__learner__in=_visible_learners(request),
    )
    return render(request, "finance/receipt.html", {"receipt": receipt})
