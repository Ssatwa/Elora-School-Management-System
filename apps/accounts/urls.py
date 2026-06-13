from django.contrib.auth.views import LogoutView
from django.urls import path

from apps.accounts.views import SchoolLoginView

app_name = "accounts"

urlpatterns = [
    path("login/", SchoolLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
]
