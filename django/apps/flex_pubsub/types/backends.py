from typing import Any, Callable, Dict, List, Optional

from pydantic import BaseModel, Field


class RequestMessage(BaseModel):
    task_name: str
    args: Optional[List[Any]] = Field(default=[])
    kwargs: Optional[Dict[str, Any]] = Field(default={})


class CallbackContext(BaseModel):
    raw_message: str
    ack: Callable[[], None]
    task: Callable[..., Any]


SubscriptionCallback = Callable[[CallbackContext], None]
