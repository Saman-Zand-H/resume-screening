from config.settings.subscriptions import NotificationSubscription
from flex_pubsub.tasks import task_registry
from notification.tasks import register_campaign_cronjobs

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Sync schedulers"

    def handle(self, **kwargs):
        register_campaign_cronjobs()
        task_registry.sync_registered_jobs(excluded_subscriptions=[NotificationSubscription.CAMPAIGN.value])
