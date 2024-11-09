from django.db.models import TextChoices
from django.utils.translation import gettext_lazy as _


class NotificationTypes(TextChoices):
    EMAIL = "email", _("Email")
    SMS = "sms", _("SMS")
    WHATSAPP = "whatsapp", _("WhatsApp")
    PUSH = "push", _("Push")
    IN_APP = "in_app", _("In-App")


SCHEDULER_TASK_NAME_TEMPLATE = "scheduler_for_campaign_%(campaign_id)s"


def scheduler_task_name(campaign_id: int) -> str:
    return SCHEDULER_TASK_NAME_TEMPLATE % {"campaign_id": campaign_id}
