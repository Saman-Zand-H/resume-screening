from django.core.checks import register

from .category import CategoryBase
from .tasks import task_registry


@register()
def sync_scheduler_configs(app_configs, **kwargs):
    task_registry.sync_registered_jobs()
    CategoryBase.validate_chosen_categories()
    return []
