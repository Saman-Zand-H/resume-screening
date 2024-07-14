from flex_pubsub.tasks import task_registry

from django.db.models import TextChoices

from .accesses import AccessContainer


class DefaultRoles(TextChoices):
    OWNER = "owner", "Owner"


def get_task_names_choices():
    return [(i, i) for i in task_registry.get_all_tasks()]


def get_access_slugs():
    return [(access.slug, access.description or access.slug) for access in AccessContainer.get_all_accesses()]
