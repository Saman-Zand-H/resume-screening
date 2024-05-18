from flex_pubsub.tasks import task_registry


def get_task_names_choices():
    return [(i, i) for i in task_registry.get_all_tasks()]
