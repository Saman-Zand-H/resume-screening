from django.core.checks import register

from .subscription import SubscriptionBase
from .tasks import task_registry


@register()
def sync_scheduler_configs(app_configs, **kwargs):
    task_registry.sync_registered_jobs()
    SubscriptionBase.validate_chosen_subscriptions()
    return []
