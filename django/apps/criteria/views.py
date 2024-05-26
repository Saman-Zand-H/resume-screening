from common.views import WebhookView
from common.webhook import WebhookEvent, WebhookHandlerResponse

from django.conf import settings

from .client.types import GetScoresResponse, GetStatusResponse
from .forms import ScoreWebhookForm, StatusWebhookForm
from .models import JobAssessmentResult


class CriteriaWebhookView(WebhookView):
    def get_webhook_secret(self):
        return settings.CRITERIA_SETTINGS["WEBHOOK_SECRET"]

    def get_webhook_header_key(self):
        return "x-criteria-api-key"


def handle_scores_update(payload: dict) -> WebhookHandlerResponse:
    scores_response = GetScoresResponse.model_validate(payload)
    result = JobAssessmentResult.objects.get(order_id=scores_response.orderId)
    result.raw_score = {k: v for k, v in scores_response.scores.model_dump().items() if v is not None}
    result.report_url = scores_response.reportUrl
    result.save(
        update_fields=[
            JobAssessmentResult.raw_score.field.name,
            JobAssessmentResult.report_url.field.name,
        ]
    )
    return WebhookHandlerResponse(status="success")


class ScoresWebhookView(CriteriaWebhookView):
    event = WebhookEvent(event="scores_update", handler=handle_scores_update)
    form_class = ScoreWebhookForm


def handle_status_update(payload: dict) -> WebhookHandlerResponse:
    status_response = GetStatusResponse.model_validate(payload)
    result = JobAssessmentResult.objects.get(order_id=status_response.orderId)
    result.raw_status = status_response.status
    result.save(update_fields=[JobAssessmentResult.raw_status.field.name])
    return WebhookHandlerResponse(status="success")


class StatusWebhookView(CriteriaWebhookView):
    event = WebhookEvent(event="status_update", handler=handle_status_update)
    form_class = StatusWebhookForm
