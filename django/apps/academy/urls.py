from django.urls import include, path

from . import views

app_name = "academy"

webhooks_patterns = [
    path("status/", views.StatusWebhookView.as_view(), name="status"),
]

urlpatterns = [
    path("webhooks/", include((webhooks_patterns, "webhooks"))),
]
