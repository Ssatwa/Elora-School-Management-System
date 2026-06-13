from django.urls import path

from apps.learning import views

app_name = "learning"
urlpatterns = [path("", views.index, name="index")]
