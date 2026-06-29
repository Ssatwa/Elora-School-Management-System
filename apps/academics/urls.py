from django.urls import path

from apps.academics import views

app_name = "academics"

urlpatterns = [
    path("", views.structure, name="structure"),
    path("create/<slug:model_name>/", views.create, name="create"),
    path(
        "stream-labels/<uuid:label_id>/delete/",
        views.delete_stream_label,
        name="delete_stream_label",
    ),
]
