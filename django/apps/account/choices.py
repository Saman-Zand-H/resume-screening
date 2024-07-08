from flex_pubsub.tasks import task_registry

from .accesses import AccessContainer


def get_task_names_choices():
    return [(i, i) for i in task_registry.get_all_tasks()]


def get_access_slugs():
    return [(access.slug, access.description or access.slug) for access in AccessContainer.get_accesses()]
