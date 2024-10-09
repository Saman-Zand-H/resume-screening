from account.tasks import user_task_decorator
from config.settings.subscriptions import CVSubscription
from flex_pubsub.tasks import register_task

from django.contrib.auth import get_user_model

from .models import CVTemplate, GeneratedCV


@register_task(subscriptions=[CVSubscription.CV])
@user_task_decorator(timeout_seconds=120)
def render_cv_template(user_id: int, template_id: int = None):
    user = get_user_model().objects.get(pk=user_id)
    template = CVTemplate.objects.filter(pk=template_id).first()

    if not hasattr(user, "profile"):
        raise ValueError("User has no profile.")

    GeneratedCV.from_user(user, template)
    return True
