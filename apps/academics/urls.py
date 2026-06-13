from django.urls import path

from apps.academics import views

app_name = "academics"

urlpatterns = [
    path("", views.structure, name="structure"),
    path("create/<slug:model_name>/", views.create, name="create"),
]
