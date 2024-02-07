from .client.types import (
    Event,
    GetScoresResponse,
    GetStatusResponse,
    WebhookHandlerResponse,
)


def handle_scores_update(payload: dict) -> WebhookHandlerResponse:
    validated_payload = GetScoresResponse.model_validate(payload)
    return WebhookHandlerResponse(status="success")


def handle_status_update(payload: dict) -> WebhookHandlerResponse:
    validated_payload = GetStatusResponse.model_validate(payload)
    return WebhookHandlerResponse(status="success")


class Events:
    SCORES_UPDATE = Event(event="scores_update", handler=handle_scores_update)
    STATUS_UPDATE = Event(event="status_update", handler=handle_status_update)


class WebhookHandler:
    @classmethod
    def handle_event(cls, event: Event, payload: dict) -> WebhookHandlerResponse:
        return event.handler(payload)
