from django.apps import AppConfig


class NotificationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "notification"

    def ready(self):
        from . import populators  # noqa
        from . import tasks  # noqa
        from . import signals  # noqa
