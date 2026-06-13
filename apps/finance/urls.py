from django.urls import path

from apps.finance import views

app_name = "finance"

urlpatterns = [
    path("", views.index, name="index"),
    path("learners/<uuid:learner_id>/statement/", views.statement, name="statement"),
    path("receipts/<uuid:receipt_id>/", views.receipt, name="receipt"),
]
