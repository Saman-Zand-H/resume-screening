from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class RequestMessage(BaseModel):
    task_name: str
    args: Optional[List[Any]] = Field(default=[])
    kwargs: Optional[Dict[str, Any]] = Field(default={})
