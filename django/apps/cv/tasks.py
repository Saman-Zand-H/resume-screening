from account.models import UserTask
from config.settings.subscriptions import CVSubscription
from flex_pubsub.tasks import register_task

from django.contrib.auth import get_user_model

from .models import CVTemplate, GeneratedCV


@register_task(subscriptions=[CVSubscription.CV])
def render_cv_template(user_id: int, template_id: int = None):
    user = get_user_model().objects.get(pk=user_id)
    template = CVTemplate.objects.filter(pk=template_id).first()
    user_task = UserTask.objects.get_or_create(user=user, task_name=render_cv_template.__name__)[0]
    if user_task.status == UserTask.TaskStatus.IN_PROGRESS:
        return False

    if not hasattr(user, "profile"):
        user_task.change_status(UserTask.TaskStatus.FAILED)
        return False

    user_task.change_status(UserTask.TaskStatus.IN_PROGRESS)
    try:
        GeneratedCV.from_user(user, template)
        user_task.change_status(UserTask.TaskStatus.COMPLETED)
        return True
    except Exception:
        user_task.change_status(UserTask.TaskStatus.FAILED)
        return False
