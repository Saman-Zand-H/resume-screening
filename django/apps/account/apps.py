from django.apps import AppConfig


class AccountConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "account"
    label = "auth_account"

    def ready(self):
        from . import observers  # noqa
        from . import populators  # noqa
        from . import scores  # noqa
        from . import signals  # noqa
        from . import tasks  # noqa
        from . import report_mapper  # noqa
        from . import context_mappers  # noqa
        from . import types  # noqa
        from .accesses import AccessContainer

        AccessContainer.register_all_rules()
