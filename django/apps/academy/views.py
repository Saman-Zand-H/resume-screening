from common.views import WebhookView
from common.webhook import WebhookEvent, WebhookHandlerResponse

from django.conf import settings

from .client.types import CollegeCourseStatus, CourseCompletaionResponse
from .forms import StatusWebhookForm
from .models import CourseResult

COURSE_RESULT_STATUS = {
    CollegeCourseStatus.PASSED: CourseResult.Status.COMPLETED,
    CollegeCourseStatus.FAILED: CourseResult.Status.FAILED,
}


class AcademyWebhookView(WebhookView):
    def get_webhook_secret(self):
        return settings.ACADEMY_SETTINGS["WEBHOOK_SECRET"]

    def get_webhook_header_key(self):
        return "x-cpj-college-api-key"


def handle_status_update(payload: dict) -> WebhookHandlerResponse:
    status_response = CourseCompletaionResponse.model_validate(payload)

    CourseResult.objects.filter(user=status_response.external_id, course__external_id=status_response.course_id).update(
        status=COURSE_RESULT_STATUS[status_response.status]
    )

    return WebhookHandlerResponse(status="success")


class StatusWebhookView(AcademyWebhookView):
    event = WebhookEvent(event="status_update", handler=handle_status_update)
    form_class = StatusWebhookForm
