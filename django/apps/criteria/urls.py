from django.urls import include, path

from . import views

app_name = "criteria"

webhooks_patterns = [
    path("scores/", views.ScoresWebhookView.as_view(), name="score"),
]

urlpatterns = [
    path("webhooks/", include((webhooks_patterns, "webhooks"))),
]
