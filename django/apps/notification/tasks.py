from common.utils import fields_join
from config.settings.subscriptions import NotificationSubscription
from croniter import croniter
from flex_pubsub.tasks import register_task

from django.utils import timezone

from .models import Campaign
from .senders import send_campaign_notifications


@register_task([NotificationSubscription.CAMPAIGN], schedule={"schedule": "0 */1 * * *"})
def run_campaign_crontabs():
    periodic_campaigns = Campaign.objects.filter(**{fields_join(Campaign.crontab, "isnull"): False})
    for campaign in periodic_campaigns:
        crontab = croniter(campaign.crontab)
        if crontab.get_prev() < (campaign.crontab_last_run or timezone.now()):
            send_campaign_notifications.delay(campaign_id=campaign.pk)
