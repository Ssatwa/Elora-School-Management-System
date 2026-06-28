from django.urls import path

from apps.accounts.views import SchoolLoginView, SchoolSelectionView, universal_logout

app_name = "accounts"

urlpatterns = [
    path("login/", SchoolLoginView.as_view(), name="login"),
    path("schools/", SchoolSelectionView.as_view(), name="select_school"),
    path("logout/", universal_logout, name="logout"),
]
