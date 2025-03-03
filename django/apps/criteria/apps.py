from django.apps import AppConfig


class CriteriaConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "criteria"

    def ready(self):
        from . import signals  # noqa
        from .client import types  # noqa: F401
