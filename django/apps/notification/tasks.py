import contextlib

from common.utils import fields_join
from config.settings.subscriptions import NotificationSubscription
from flex_pubsub.tasks import register_task, task_registry
from flex_pubsub.types import SchedulerJob

from django.db.models.lookups import IsNull
from django.utils import timezone

from .models import Campaign
from .senders import send_campaign_notifications


def sync_campaign_scheduler_task():
    active_campaigns = Campaign.objects.filter(
        **{fields_join(Campaign.is_scheduler_active): True, fields_join(Campaign.crontab, IsNull.lookup_name): False}
    )
    for campaign in active_campaigns:
        register_campaign_cronjob(campaign)

    inactive_campaigns = Campaign.objects.all().difference(active_campaigns)
    for campaign in inactive_campaigns:
        with contextlib.suppress(KeyError):
            del task_registry.tasks[f"scheduler_for_campaign_{campaign.pk}"]

    task_registry.sync_registered_jobs()


def send_campaign_notifications_cronjob(campaign_id: int):
    if not Campaign.objects.filter(
        **{Campaign._meta.pk.attname: campaign_id, fields_join(Campaign.is_scheduler_active): True}
    ).exists():
        return

    send_campaign_notifications(campaign_id=campaign_id)
    Campaign.objects.filter(pk=campaign_id).update(**{fields_join(Campaign.crontab_last_run): timezone.now()})


def register_campaign_cronjob(campaign: Campaign):
    task_name = f"scheduler_for_campaign_{campaign.pk}"

    return register_task(
        [NotificationSubscription.CAMPAIGN],
        schedule=SchedulerJob(schedule=campaign.crontab, kwargs={"campaign_id": campaign.pk}),
        name=task_name,
    )(send_campaign_notifications_cronjob)


def register_campaign_cronjobs():
    campaigns = Campaign.objects.filter(
        **{fields_join(Campaign.crontab, IsNull.lookup_name): False, fields_join(Campaign.is_scheduler_active): True}
    )

    for campaign in campaigns:
        register_campaign_cronjob(campaign)
