from django.apps import AppConfig


class FlexPubsubConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "flex_pubsub"

    def ready(self):
        from . import checks  # noqa: F401
