from django.urls import path
from django.views.generic import RedirectView

from .views import health, readiness

urlpatterns = [
    path(
        "",
        RedirectView.as_view(pattern_name="analytics:dashboard", permanent=False),
        name="home",
    ),
    path("health/", health, name="health"),
    path("ready/", readiness, name="readiness"),
]
