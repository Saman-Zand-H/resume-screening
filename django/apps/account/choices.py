from flex_pubsub.tasks import task_registry

from django.db.models import TextChoices
from django.utils.translation import gettext_lazy as _


class ContactType(TextChoices):
    WEBSITE = "website", _("Website")
    ADDRESS = "address", _("Address")
    LINKEDIN = "linkedin", _("LinkedIn")
    WHATSAPP = "whatsapp", _("WhatsApp")
    PHONE = "phone", _("Phone")


class DefaultRoles(TextChoices):
    OWNER = "owner", "Owner"


def get_task_names_choices():
    return [(i, i) for i in task_registry.get_all_tasks()]
