from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from apps.accounts.audit import record_audit_event
from apps.accounts.permissions import has_school_role
from apps.finance.models import Invoice, Payment, PaymentAllocation, Receipt


def _require_finance_role(actor, school):
    if not has_school_role(actor, school, "accountant", "school_admin", "principal"):
        raise PermissionDenied("Finance permission is required.")


def _next_number(model, school, prefix):
    return f"{prefix}-{school.slug.upper()[:4]}-{model.objects.for_school(school).count() + 1:06d}"


@transaction.atomic
def create_invoice(*, school, actor, learner, term, description, amount, due_date):
    _require_finance_role(actor, school)
    if learner.school_id != school.id or term.school_id != school.id:
        raise ValidationError("Invoice records must belong to the same school.")
    invoice = Invoice.objects.create(
        school=school,
        learner=learner,
        term=term,
        invoice_number=_next_number(Invoice, school, "INV"),
        description=description,
        amount=amount,
        due_date=due_date,
        created_by=actor,
    )
    record_audit_event(
        school=school,
        actor=actor,
        action="finance.invoice.created",
        target_type="finance.Invoice",
        target_id=invoice.id,
        metadata={"amount": str(amount), "learner_id": str(learner.id)},
    )
    return invoice


@transaction.atomic
def record_payment(*, school, actor, learner, amount, method, reference, paid_on):
    _require_finance_role(actor, school)
    if learner.school_id != school.id:
        raise ValidationError("Payment learner must belong to the same school.")
    return Payment.objects.create(
        school=school,
        learner=learner,
        payment_number=_next_number(Payment, school, "PAY"),
        amount=amount,
        method=method,
        reference=reference,
        paid_on=paid_on,
        received_by=actor,
    )


@transaction.atomic
def allocate_payment(*, school, actor, payment, invoice, amount):
    _require_finance_role(actor, school)
    payment = Payment.objects.select_for_update().get(pk=payment.pk)
    invoice = Invoice.objects.select_for_update().get(pk=invoice.pk)
    if payment.school_id != school.id or invoice.school_id != school.id:
        raise ValidationError("Finance records must belong to the same school.")
    if payment.learner_id != invoice.learner_id:
        raise ValidationError("Payment and invoice must belong to the same learner.")
    if amount <= 0 or amount > payment.unallocated_amount or amount > invoice.balance:
        raise ValidationError("Allocation exceeds the available payment or invoice balance.")
    allocation = PaymentAllocation.objects.create(
        school=school,
        payment=payment,
        invoice=invoice,
        amount=amount,
        allocated_by=actor,
    )
    balance = invoice.balance
    invoice.status = (
        Invoice.Status.PAID
        if balance == 0
        else Invoice.Status.PART_PAID
    )
    invoice.save(update_fields=["status", "updated_at"])
    receipt = Receipt.objects.create(
        school=school,
        allocation=allocation,
        receipt_number=_next_number(Receipt, school, "RCT"),
        amount=amount,
        issued_by=actor,
    )
    record_audit_event(
        school=school,
        actor=actor,
        action="finance.payment.allocated",
        target_type="finance.PaymentAllocation",
        target_id=allocation.id,
        metadata={"invoice_id": str(invoice.id), "amount": str(amount)},
    )
    return receipt
