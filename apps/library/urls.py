from django.urls import path

from apps.library import views

app_name = "library"
urlpatterns = [path("", views.index, name="index")]
