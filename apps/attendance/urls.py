from django.urls import path

from apps.attendance import views

app_name = "attendance"

urlpatterns = [
    path("", views.index, name="index"),
    path("register/learners/", views.learner_register, name="learner-register"),
    path("register/staff/", views.staff_register, name="staff-register"),
    path(
        "entries/learners/<uuid:entry_id>/correct/",
        views.correct_learner_entry,
        name="correct-learner-entry",
    ),
    path(
        "entries/staff/<uuid:entry_id>/correct/",
        views.correct_staff_entry,
        name="correct-staff-entry",
    ),
    path("export/", views.export, name="export"),
]
