from django.db import models

from apps.core.models import TimeStampedModel, UUIDModel
from apps.tenancy.managers import TenantManager


class LibraryBook(UUIDModel, TimeStampedModel):
    school = models.ForeignKey("tenancy.School", on_delete=models.CASCADE)
    isbn = models.CharField(max_length=20)
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=160)
    category = models.CharField(max_length=100, blank=True)
    total_copies = models.PositiveIntegerField(default=1)
    available_copies = models.PositiveIntegerField(default=1)

    objects = TenantManager()

    class Meta:
        ordering = ["title"]
        constraints = [
            models.UniqueConstraint(
                fields=["school", "isbn"],
                name="unique_school_book_isbn",
            )
        ]

    def __str__(self):
        return self.title


class BorrowRecord(UUIDModel, TimeStampedModel):
    class Status(models.TextChoices):
        BORROWED = "borrowed", "Borrowed"
        RETURNED = "returned", "Returned"
        OVERDUE = "overdue", "Overdue"

    school = models.ForeignKey("tenancy.School", on_delete=models.CASCADE)
    book = models.ForeignKey(LibraryBook, on_delete=models.PROTECT, related_name="loans")
    learner = models.ForeignKey("learners.Learner", on_delete=models.PROTECT)
    borrowed_by = models.ForeignKey("accounts.User", on_delete=models.PROTECT)
    borrowed_at = models.DateField(auto_now_add=True)
    due_date = models.DateField()
    returned_at = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.BORROWED)
    fine_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    objects = TenantManager()

    class Meta:
        ordering = ["-borrowed_at"]
        indexes = [models.Index(fields=["school", "status", "due_date"])]
