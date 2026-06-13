from django.urls import path

from apps.wellbeing import views

app_name = "wellbeing"
urlpatterns = [path("", views.index, name="index")]
