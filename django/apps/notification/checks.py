from django.core.checks import register

from .tasks import sync_campaign_scheduler_task


@register()
def sync_campaign_schedulers_check(*args, **kwargs):
    sync_campaign_scheduler_task()
    return []
