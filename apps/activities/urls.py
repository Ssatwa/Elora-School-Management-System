from django.urls import path

from apps.activities import views

app_name = "activities"
urlpatterns = [path("", views.index, name="index")]
