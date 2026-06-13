from django.urls import path

from apps.timetabling import views

app_name = "timetabling"

urlpatterns = [
    path("", views.index, name="index"),
    path("create/", views.create_timetable, name="create-timetable"),
    path("setup/<slug:setup_type>/", views.create_setup, name="create-setup"),
    path("mine/", views.my_schedule, name="my-schedule"),
    path("classes/<uuid:stream_id>/", views.class_schedule, name="class-schedule"),
    path("<uuid:timetable_id>/", views.detail, name="detail"),
    path("<uuid:timetable_id>/entries/", views.add_entry, name="add-entry"),
    path("<uuid:timetable_id>/publish/", views.publish, name="publish"),
]
