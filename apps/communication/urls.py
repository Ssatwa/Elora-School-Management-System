from django.urls import path

from apps.communication import views

app_name = "communication"
urlpatterns = [path("", views.index, name="index")]
