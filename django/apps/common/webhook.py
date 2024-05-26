from typing import Callable, TypedDict

from pydantic import BaseModel


class WebhookHandlerResponse(TypedDict):
    status: str


class WebhookEvent(BaseModel):
    event: str
    handler: Callable[[dict], WebhookHandlerResponse]


class WebhookHandler:
    @classmethod
    def handle_event(cls, event: WebhookEvent, payload: dict) -> WebhookHandlerResponse:
        return event.handler(payload)
