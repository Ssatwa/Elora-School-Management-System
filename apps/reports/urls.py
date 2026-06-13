from django.urls import path

from apps.reports import views

app_name = "reports"

urlpatterns = [
    path("", views.index, name="index"),
    path("<uuid:report_id>/download/", views.download, name="download"),
]
