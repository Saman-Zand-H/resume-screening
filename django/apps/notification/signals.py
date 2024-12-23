from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Campaign
from .tasks import sync_campaign_scheduler_task


@receiver(post_save, sender=Campaign)
@receiver(post_delete, sender=Campaign)
def sync_campaign_schedulers(sender, instance: Campaign, created, **kwargs):
    if not (instance.crontab and instance.is_scheduler_active):
        return

    sync_campaign_scheduler_task()
