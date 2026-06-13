from django.urls import path

from apps.analytics.views import dashboard

app_name = "analytics"

urlpatterns = [
    path("dashboard/", dashboard, name="dashboard"),
]
