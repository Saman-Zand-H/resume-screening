from django.urls import path

from . import views

app_name = "criteria"

urlpatterns = [
    path("webhooks/scores/", views.ScoresUpdateWebhookView.as_view(), name="webhook_score"),
]
