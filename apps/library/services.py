from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from apps.accounts.permissions import has_school_role
from apps.library.models import BorrowRecord, LibraryBook


def _require_librarian(actor, school):
    if not has_school_role(actor, school, "librarian", "school_admin"):
        raise PermissionDenied("Library permission is required.")


@transaction.atomic
def borrow_book(*, school, actor, book, learner, due_date):
    _require_librarian(actor, school)
    locked = LibraryBook.objects.select_for_update().get(pk=book.pk)
    if locked.school_id != school.id or learner.school_id != school.id:
        raise ValidationError("Book and learner must belong to the same school.")
    if locked.available_copies < 1:
        raise ValidationError("No copy is available.")
    locked.available_copies -= 1
    locked.save(update_fields=["available_copies", "updated_at"])
    return BorrowRecord.objects.create(
        school=school,
        book=locked,
        learner=learner,
        borrowed_by=actor,
        due_date=due_date,
    )


@transaction.atomic
def return_book(*, school, actor, loan):
    _require_librarian(actor, school)
    locked = BorrowRecord.objects.select_for_update().select_related("book").get(pk=loan.pk)
    if locked.school_id != school.id or locked.status == BorrowRecord.Status.RETURNED:
        raise ValidationError("Loan cannot be returned.")
    locked.status = BorrowRecord.Status.RETURNED
    locked.returned_at = timezone.localdate()
    locked.save(update_fields=["status", "returned_at", "updated_at"])
    locked.book.available_copies += 1
    locked.book.save(update_fields=["available_copies", "updated_at"])
    return locked
