from collections.abc import Callable
from typing import TypedDict

from pydantic import BaseModel


class WebhookHandlerResponse(TypedDict):
    status: str


class Event(BaseModel):
    event: str
    handler: Callable[[dict], WebhookHandlerResponse]
