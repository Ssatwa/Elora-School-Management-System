from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.accounts.decorators import school_roles_required
from apps.library.models import BorrowRecord, LibraryBook


@login_required
@school_roles_required("librarian", "school_admin", "principal")
def index(request):
    return render(
        request,
        "library/index.html",
        {
            "books": LibraryBook.objects.for_school(request.school)[:30],
            "loans": BorrowRecord.objects.for_school(request.school)
            .select_related("book", "learner")[:15],
        },
    )
