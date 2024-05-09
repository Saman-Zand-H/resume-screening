from django.urls import include, path

from . import views

app_name = "criteria"

webhooks_patterns = [
    path("scores/", views.ScoresWebhookView.as_view(), name="score"),
    path("status/", views.StatusWebhookView.as_view(), name="status"),
]

urlpatterns = [
    path("webhooks/", include((webhooks_patterns, "webhooks"))),
]
