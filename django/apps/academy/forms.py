from common.forms import WebhookForm

from .client.types import CourseCompletaionResponse


class StatusWebhookForm(WebhookForm):
    model = CourseCompletaionResponse
