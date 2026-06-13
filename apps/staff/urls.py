from django.urls import path

from apps.staff import views

app_name = "staff"

urlpatterns = [
    path("", views.index, name="index"),
    path("create/<slug:model_name>/", views.create, name="create"),
]
