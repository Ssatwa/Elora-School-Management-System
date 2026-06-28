from django.urls import path

from apps.learners import views

app_name = "learners"

urlpatterns = [
    path("", views.index, name="index"),
    path("admit/", views.admit, name="admit"),
    path("admit/bulk/", views.bulk_admit, name="bulk_admit"),
    path("admit/bulk/confirm/", views.bulk_admit_confirm, name="bulk_admit_confirm"),
    path("admit/bulk/template/", views.bulk_admit_template, name="bulk_admit_template"),
    path("<uuid:learner_id>/", views.detail, name="detail"),
    path("<uuid:learner_id>/transfer/", views.transfer, name="transfer"),
]
