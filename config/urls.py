from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("", include("apps.core.urls")),
    path("", include("apps.analytics.urls")),
    path("accounts/", include("apps.accounts.urls")),
    path("academics/", include("apps.academics.urls")),
    path("staff/", include("apps.staff.urls")),
    path("learners/", include("apps.learners.urls")),
    path("attendance/", include("apps.attendance.urls")),
    path("timetables/", include("apps.timetabling.urls")),
    path("admin/", admin.site.urls),
]
