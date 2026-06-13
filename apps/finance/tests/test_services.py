from datetime import date
from decimal import Decimal

import pytest
from django.core.exceptions import PermissionDenied, ValidationError

from apps.academics.models import AcademicYear, Grade, Stream, Term
from apps.finance.services import allocate_payment, create_invoice, record_payment
from apps.learners.models import Enrollment, Learner
from tests.factories import MembershipFactory, SchoolFactory

pytestmark = pytest.mark.django_db


def setup_finance():
    school = SchoolFactory()
    year = AcademicYear.objects.create(
        school=school,
        name="2026",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
        status=AcademicYear.Status.ACTIVE,
    )
    term = Term.objects.create(
        school=school,
        academic_year=year,
        name="Term 2",
        sequence=2,
        start_date=date(2026, 5, 4),
        end_date=date(2026, 8, 7),
    )
    grade = Grade.objects.create(
        school=school,
        code="G7",
        name="Grade 7",
        education_level=Grade.EducationLevel.JUNIOR_SCHOOL,
        order=7,
    )
    stream = Stream.objects.create(
        school=school,
        grade=grade,
        code="E",
        name="East",
    )
    learner = Learner.objects.create(
        school=school,
        admission_number="2026-0001",
        first_name="Amina",
        last_name="Kamau",
        date_of_birth=date(2013, 6, 12),
        gender=Learner.Gender.FEMALE,
        admission_date=date(2026, 1, 6),
    )
    Enrollment.objects.create(
        school=school,
        learner=learner,
        academic_year=year,
        grade=grade,
        stream=stream,
        start_date=date(2026, 1, 6),
    )
    accountant = MembershipFactory(school=school, role_code="accountant")
    return school, term, learner, accountant


def test_accountant_invoices_allocates_payment_and_issues_receipt():
    school, term, learner, accountant = setup_finance()
    invoice = create_invoice(
        school=school,
        actor=accountant.user,
        learner=learner,
        term=term,
        description="Term 2 tuition",
        amount=Decimal("25000.00"),
        due_date=date(2026, 5, 31),
    )
    payment = record_payment(
        school=school,
        actor=accountant.user,
        learner=learner,
        amount=Decimal("10000.00"),
        method="bank",
        reference="BANK-001",
        paid_on=date(2026, 5, 15),
    )
    receipt = allocate_payment(
        school=school,
        actor=accountant.user,
        payment=payment,
        invoice=invoice,
        amount=Decimal("10000.00"),
    )

    invoice.refresh_from_db()
    assert invoice.balance == Decimal("15000.00")
    assert receipt.receipt_number.startswith("RCT-")
    assert receipt.amount == Decimal("10000.00")


def test_payment_is_immutable_and_over_allocation_is_rejected():
    school, term, learner, accountant = setup_finance()
    invoice = create_invoice(
        school=school,
        actor=accountant.user,
        learner=learner,
        term=term,
        description="Tuition",
        amount=Decimal("5000.00"),
        due_date=date(2026, 5, 31),
    )
    payment = record_payment(
        school=school,
        actor=accountant.user,
        learner=learner,
        amount=Decimal("3000.00"),
        method="cash",
        reference="CASH-001",
        paid_on=date(2026, 5, 15),
    )
    payment.amount = Decimal("4000.00")
    with pytest.raises(ValidationError):
        payment.save()
    with pytest.raises(ValidationError):
        allocate_payment(
            school=school,
            actor=accountant.user,
            payment=payment,
            invoice=invoice,
            amount=Decimal("3500.00"),
        )


def test_teacher_cannot_record_finance_transactions():
    school, term, learner, _ = setup_finance()
    teacher = MembershipFactory(school=school, role_code="teacher")

    with pytest.raises(PermissionDenied):
        create_invoice(
            school=school,
            actor=teacher.user,
            learner=learner,
            term=term,
            description="Tuition",
            amount=Decimal("5000.00"),
            due_date=date(2026, 5, 31),
        )
