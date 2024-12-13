import contextlib

from common.logging import get_logger
from common.utils import fj
from config.settings.subscriptions import NotificationSubscription
from flex_pubsub.tasks import register_task, task_registry
from flex_pubsub.types import SchedulerJob

from django.db.models.lookups import IsNull
from django.utils import timezone

from .constants import scheduler_task_name
from .models import Campaign
from .senders import send_campaign_notifications

logger = get_logger()


def sync_campaign_scheduler_task():
    active_campaigns = Campaign.objects.filter(
        **{fj(Campaign.is_scheduler_active): True, fj(Campaign.crontab, IsNull.lookup_name): False}
    )
    for campaign in active_campaigns:
        register_campaign_cronjob(campaign)

    inactive_campaigns = Campaign.objects.all().difference(active_campaigns)
    for campaign in inactive_campaigns:
        with contextlib.suppress(KeyError):
            del task_registry.tasks[scheduler_task_name(campaign.pk)]

    task_registry.sync_registered_jobs()


def send_campaign_notifications_cronjob(campaign_id: int):
    if not Campaign.objects.filter(
        **{Campaign._meta.pk.attname: campaign_id, fj(Campaign.is_scheduler_active): True}
    ).exists():
        return

    logger.info(f"Received campaign task for id: {campaign_id}. Executing...")
    send_campaign_notifications(campaign_id=campaign_id)
    logger.info(f"Finished campaign task for id: {campaign_id}.")
    Campaign.objects.filter(**{Campaign._meta.pk.attname: campaign_id}).update(
        **{fj(Campaign.crontab_last_run): timezone.now()}
    )


def register_campaign_cronjob(campaign: Campaign):
    task_name = scheduler_task_name(campaign.pk)

    return register_task(
        [NotificationSubscription.CAMPAIGN],
        schedule=SchedulerJob(schedule=campaign.crontab, kwargs={"campaign_id": campaign.pk}),
        name=task_name,
    )(send_campaign_notifications_cronjob)


def register_campaign_cronjobs():
    campaigns = Campaign.objects.filter(
        **{
            fj(Campaign.is_scheduler_active): True,
            fj(Campaign.crontab, IsNull.lookup_name): False,
        }
    )

    for campaign in campaigns:
        register_campaign_cronjob(campaign)
