from typing import Any, Dict, List, Optional

from .app_settings import app_settings
from .types import RequestMessage
from .utils import are_categories_valid


def send_task(
    *args: Optional[List[Any]],
    task_name: str,
    categories: List[str] = [],
    **kwargs: Optional[Dict[str, Any]],
) -> None:
    args = args or []
    kwargs = kwargs or {}
    if not are_categories_valid(categories):
        return

    raw_message = {
        "task_name": task_name,
        "args": args,
        "kwargs": kwargs,
    }
    message_str = RequestMessage.model_validate(raw_message).model_dump_json()
    backend_class = app_settings.BACKEND_CLASS
    backend = backend_class()
    backend.publish(message_str)
