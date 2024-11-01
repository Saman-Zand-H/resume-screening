from common.utils import fields_join
from config.settings.subscriptions import NotificationSubscription
from croniter import croniter
from flex_pubsub.tasks import register_task

from django.db.models.lookups import IsNull
from django.utils import timezone

from .constants import SCHEDULER_CRONJOB_DIFFERENCE_THRESHOLD
from .models import Campaign
from .senders import send_campaign_notifications


@register_task([NotificationSubscription.CAMPAIGN], schedule={"schedule": "0 */1 * * *"})
def run_campaign_crontabs():
    periodic_campaigns = Campaign.objects.filter(
        **{
            fields_join(Campaign.crontab, IsNull.lookup_name): False,
            fields_join(Campaign.is_scheduler_active): True,
        }
    )

    for campaign in periodic_campaigns:
        crontab = croniter(campaign.crontab)
        if (
            abs(crontab.get_next(timezone.datetime) - (campaign.crontab_last_run or timezone.now()))
            <= SCHEDULER_CRONJOB_DIFFERENCE_THRESHOLD
        ):
            send_campaign_notifications(campaign)
            campaign.crontab_last_run = timezone.now()
            campaign.save(update_fields=[fields_join(Campaign.crontab_last_run)])
