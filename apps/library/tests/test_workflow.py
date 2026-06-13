from datetime import date, timedelta

import pytest
from django.urls import reverse

from apps.assessments.tests.test_models import make_learner
from apps.library.models import BorrowRecord, LibraryBook
from apps.library.services import borrow_book, return_book
from tests.factories import MembershipFactory, SchoolFactory

pytestmark = pytest.mark.django_db


def test_librarian_borrows_and_returns_book(client):
    school = SchoolFactory()
    librarian = MembershipFactory(school=school, role_code="librarian")
    learner = make_learner(school)
    book = LibraryBook.objects.create(
        school=school,
        isbn="978000000001",
        title="CBC Mathematics",
        author="Elora Press",
        total_copies=2,
        available_copies=2,
    )
    loan = borrow_book(
        school=school,
        actor=librarian.user,
        book=book,
        learner=learner,
        due_date=date.today() + timedelta(days=14),
    )
    return_book(school=school, actor=librarian.user, loan=loan)

    book.refresh_from_db()
    loan.refresh_from_db()
    assert book.available_copies == 2
    assert loan.status == BorrowRecord.Status.RETURNED
    client.force_login(librarian.user)
    assert client.get(
        reverse("library:index"),
        HTTP_HOST=f"{school.slug}.localhost",
    ).status_code == 200
