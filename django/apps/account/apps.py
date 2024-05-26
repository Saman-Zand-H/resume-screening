from django.apps import AppConfig


class AccountConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "account"
    label = "auth_account"

    def ready(self):
        from . import observers  # noqa
        from . import scores  # noqa
        from . import signals  # noqa
        from . import tasks  # noqa
        from . import types  # noqa
