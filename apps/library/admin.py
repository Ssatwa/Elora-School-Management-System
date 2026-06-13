from django.contrib import admin

from apps.library.models import BorrowRecord, LibraryBook

admin.site.register(LibraryBook)
admin.site.register(BorrowRecord)
