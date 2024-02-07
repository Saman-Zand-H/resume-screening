import re
from enum import Enum
from typing import Optional

from pydantic import (
    BaseModel,
    RootModel,
    field_validator,
)


class GetStatusRequest(RootModel):
    root: str


class Status(Enum):
    IN_PROGRESS = "In Progress"
    SCHEDULED = "Scheduled"
    COMPLETE = "Complete"
    EVALUATION_IN_PROGRESS = r"Evaluation in Progress - \d+ of \d+ Completed"


class GetStatusResponse(BaseModel):
    orderId: str
    eventId: str
    externalId: Optional[str] = None
    status: str
    expiryDate: Optional[str] = None
    statusDate: str

    @field_validator("status")
    def validate_dynamic_status(cls, v):
        if v in [Status.IN_PROGRESS.value, Status.SCHEDULED.value, Status.COMPLETE.value]:
            return v

        if re.match(Status.EVALUATION_IN_PROGRESS.value, v):
            return v
        raise ValueError("Invalid status format")
