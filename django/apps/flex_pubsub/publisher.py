from typing import Any, Dict, List, Optional

from .app_settings import app_settings
from .types import RequestMessage


def send_task(task_name: str, args: Optional[List[Any]] = None, kwargs: Optional[Dict[str, Any]] = None) -> None:
    args = args or []
    kwargs = kwargs or {}
    raw_message = {
        "task_name": task_name,
        "args": args,
        "kwargs": kwargs,
    }
    message_str = RequestMessage.model_validate(raw_message).model_dump_json()
    backend_class = app_settings.BACKEND_CLASS
    backend = backend_class()
    backend.publish(message_str)
