from django.db.models import TextChoices
from django.utils.translation import gettext_lazy as _


class NotificationTypes(TextChoices):
    EMAIL = "email", _("Email")
    SMS = "sms", _("SMS")
    PUSH = "push", _("Push")
    IN_APP = "in_app", _("In-App")
