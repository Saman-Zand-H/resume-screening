from typing import Literal, Optional

from pydantic import BaseModel, HttpUrl, RootModel, field_validator


class GetStatusRequest(RootModel):
    root: str


class GetStatusResponse(BaseModel):
    orderId: str
    eventId: str
    externalId: Optional[str] = None
    status: Literal["In Progress", "Scheduled", "Complete", "Evaluation in Progress - X of Y Completed"]
    expiryDate: Optional[str] = None
    statusDate: str
    evaluationUrl: Optional[HttpUrl] = None
    reportUrl: Optional[HttpUrl] = None

    @field_validator("status")
    def validate_dynamic_status(cls, v):
        import re

        if v in ["In Progress", "Scheduled", "Complete"]:
            return v

        if re.match(r"^Evaluation in Progress - \d+ of \d+ Completed$", v):
            return v
        raise ValueError("Invalid status format. Expected 'Evaluation in Progress - X of Y Completed' with digits.")
