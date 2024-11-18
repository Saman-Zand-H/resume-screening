from account.tasks import user_task_decorator
from config.settings.subscriptions import CVSubscription
from flex_pubsub.tasks import register_task

from django.contrib.auth import get_user_model

from .models import CVTemplate, GeneratedCV


@register_task(subscriptions=[CVSubscription.CV])
@user_task_decorator(timeout_seconds=120)
def render_cv_template(user_id: int, template_id: int = None):
    from account.models import Profile, User

    user = get_user_model().objects.get(**{User._meta.pk.attname: user_id})
    template = CVTemplate.objects.filter(**{CVTemplate._meta.pk.attname: template_id}).first()

    if not hasattr(user, Profile.user.field.related_query_name()):
        raise ValueError("User has no profile.")

    GeneratedCV.from_user(user, template)
    return True
