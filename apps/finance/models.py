from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum

from apps.core.models import TimeStampedModel, UUIDModel
from apps.tenancy.managers import TenantManager


class FeeStructure(UUIDModel, TimeStampedModel):
    school = models.ForeignKey("tenancy.School", on_delete=models.CASCADE)
    term = models.ForeignKey("academics.Term", on_delete=models.PROTECT)
    grade = models.ForeignKey("academics.Grade", on_delete=models.PROTECT)
    name = models.CharField(max_length=160)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    is_active = models.BooleanField(default=True)

    objects = TenantManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["school", "term", "grade", "name"],
                name="unique_fee_structure_per_grade_term",
            )
        ]

    def __str__(self):
        return self.name


class Invoice(UUIDModel, TimeStampedModel):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        PART_PAID = "part_paid", "Part paid"
        PAID = "paid", "Paid"
        VOID = "void", "Void"

    school = models.ForeignKey("tenancy.School", on_delete=models.CASCADE)
    learner = models.ForeignKey("learners.Learner", on_delete=models.PROTECT)
    term = models.ForeignKey("academics.Term", on_delete=models.PROTECT)
    invoice_number = models.CharField(max_length=40)
    description = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    due_date = models.DateField()
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.OPEN)
    created_by = models.ForeignKey("accounts.User", on_delete=models.PROTECT)

    objects = TenantManager()

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["school", "invoice_number"],
                name="unique_school_invoice_number",
            )
        ]
        indexes = [models.Index(fields=["school", "learner", "status"])]

    @property
    def allocated_amount(self):
        return self.allocations.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

    @property
    def balance(self):
        return self.amount - self.allocated_amount

    def __str__(self):
        return self.invoice_number


class Payment(UUIDModel, TimeStampedModel):
    class Method(models.TextChoices):
        CASH = "cash", "Cash"
        BANK = "bank", "Bank"
        MOBILE = "mobile", "Mobile money"
        CHEQUE = "cheque", "Cheque"

    school = models.ForeignKey("tenancy.School", on_delete=models.CASCADE)
    learner = models.ForeignKey("learners.Learner", on_delete=models.PROTECT)
    payment_number = models.CharField(max_length=40)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    method = models.CharField(max_length=16, choices=Method.choices)
    reference = models.CharField(max_length=100)
    paid_on = models.DateField()
    received_by = models.ForeignKey("accounts.User", on_delete=models.PROTECT)
    reversed_at = models.DateTimeField(null=True, blank=True)
    reversal_reason = models.TextField(blank=True)

    objects = TenantManager()

    class Meta:
        ordering = ["-paid_on", "-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["school", "payment_number"],
                name="unique_school_payment_number",
            ),
            models.UniqueConstraint(
                fields=["school", "reference"],
                name="unique_school_payment_reference",
            ),
        ]

    @property
    def unallocated_amount(self):
        allocated = self.allocations.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
        return self.amount - allocated

    def save(self, *args, **kwargs):
        if not self._state.adding:
            stored = type(self).objects.get(pk=self.pk)
            immutable = ("school_id", "learner_id", "amount", "method", "reference", "paid_on")
            if any(getattr(stored, field) != getattr(self, field) for field in immutable):
                raise ValidationError("Payment transaction fields are immutable.")
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.payment_number


class PaymentAllocation(UUIDModel, TimeStampedModel):
    school = models.ForeignKey("tenancy.School", on_delete=models.CASCADE)
    payment = models.ForeignKey(Payment, on_delete=models.PROTECT, related_name="allocations")
    invoice = models.ForeignKey(Invoice, on_delete=models.PROTECT, related_name="allocations")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    allocated_by = models.ForeignKey("accounts.User", on_delete=models.PROTECT)

    objects = TenantManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["school", "payment", "invoice"],
                name="unique_payment_invoice_allocation",
            )
        ]

    def __str__(self):
        return f"{self.payment} -> {self.invoice}"


class Receipt(UUIDModel, TimeStampedModel):
    school = models.ForeignKey("tenancy.School", on_delete=models.CASCADE)
    allocation = models.OneToOneField(
        PaymentAllocation,
        on_delete=models.PROTECT,
        related_name="receipt",
    )
    receipt_number = models.CharField(max_length=40)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    issued_by = models.ForeignKey("accounts.User", on_delete=models.PROTECT)
    issued_at = models.DateTimeField(auto_now_add=True)

    objects = TenantManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["school", "receipt_number"],
                name="unique_school_receipt_number",
            )
        ]

    def __str__(self):
        return self.receipt_number
