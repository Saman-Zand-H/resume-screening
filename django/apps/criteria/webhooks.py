from .client.types import (
    Event,
    GetScoresResponse,
    GetStatusResponse,
    WebhookHandlerResponse,
)
from .models import JobAssessmentResult


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


def handle_status_update(payload: dict) -> WebhookHandlerResponse:
    status_response = GetStatusResponse.model_validate(payload)
    result = JobAssessmentResult.objects.get(order_id=status_response.orderId)
    result.raw_status = status_response.status
    result.save(update_fields=[JobAssessmentResult.raw_status.field.name])
    return WebhookHandlerResponse(status="success")


class Events:
    SCORES_UPDATE = Event(event="scores_update", handler=handle_scores_update)
    STATUS_UPDATE = Event(event="status_update", handler=handle_status_update)


class WebhookHandler:
    @classmethod
    def handle_event(cls, event: Event, payload: dict) -> WebhookHandlerResponse:
        return event.handler(payload)
