from django.urls import path

from apps.assessments import views

app_name = "assessments"

urlpatterns = [
    path("", views.index, name="index"),
    path("<uuid:assessment_id>/moderate/", views.moderate, name="moderate"),
    path("<uuid:assessment_id>/approve/", views.approve, name="approve"),
]
