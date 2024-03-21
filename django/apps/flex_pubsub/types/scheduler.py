from typing import Optional

from pydantic import BaseModel, Field

from ..app_settings import app_settings


class SchedulerJob(BaseModel):
    schedule: str
    time_zone: Optional[str] = Field(default="PST")
    pubsub_topic: str = Field(default=app_settings.TOPIC_NAME)
    args: Optional[list] = Field(default=[])
    kwargs: Optional[dict] = Field(default={})
