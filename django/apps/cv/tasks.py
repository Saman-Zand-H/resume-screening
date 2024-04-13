from config.settings.subscriptions import CVSubscription
from flex_pubsub.tasks import register_task

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

from .models import CVTemplate


@register_task(subscriptions=[CVSubscription.CV])
def render_cv_template(template_id: int, context: dict, target_file_name: str):
    template = CVTemplate.objects.get(pk=template_id)
    rendered_content = template.render_pdf(context, target_file_name)
    default_storage.save(target_file_name, ContentFile(rendered_content))
