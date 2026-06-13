from django.urls import path

from apps.learners import views

app_name = "learners"

urlpatterns = [
    path("", views.index, name="index"),
    path("admit/", views.admit, name="admit"),
    path("<uuid:learner_id>/", views.detail, name="detail"),
    path("<uuid:learner_id>/transfer/", views.transfer, name="transfer"),
]
