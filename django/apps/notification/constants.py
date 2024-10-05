from datetime import timedelta

from django.db.models import TextChoices
from django.utils.translation import gettext_lazy as _

SCHEDULER_CRONJOB_DIFFERENCE_THRESHOLD = timedelta(minutes=5)


class NotificationTypes(TextChoices):
    EMAIL = "email", _("Email")
    SMS = "sms", _("SMS")
    WHATSAPP = "whatsapp", _("WhatsApp")
    PUSH = "push", _("Push")
    IN_APP = "in_app", _("In-App")
