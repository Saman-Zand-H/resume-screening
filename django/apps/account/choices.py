from flex_pubsub.tasks import task_registry

from django.db.models import TextChoices


class DefaultRoles(TextChoices):
    OWNER = "owner", "Owner"


def get_task_names_choices():
    return [(i, i) for i in task_registry.get_all_tasks()]
