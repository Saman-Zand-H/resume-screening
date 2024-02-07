from typing import Optional

from pydantic import BaseModel, EmailStr, HttpUrl


class Identifier(BaseModel):
    value: str


class Candidate(BaseModel):
    first: str
    last: str
    email: Optional[EmailStr] = None


class ReturnURL(BaseModel):
    uri: HttpUrl


class AssessmentAccessURL(BaseModel):
    uri: HttpUrl


class CreateOrderRequest(BaseModel):
    packageId: Identifier
    orderId: Identifier
    requisitionId: Optional[Identifier] = None
    externalId: Optional[Identifier] = None
    candidate: Optional[Candidate] = None
    sendCandidateEmail: bool = False
    returnURL: Optional[ReturnURL] = None
    expiryDate: Optional[str] = None


class CreateOrderResponse(BaseModel):
    assessmentAccessURL: AssessmentAccessURL
    expiryDate: Optional[str] = None
