import dataclasses
from typing import Optional

from google.genai.errors import APIError
from graphql_jwt.exceptions import PermissionDenied as JWTPermissionDenied
from rest_framework import status
from rest_framework.exceptions import ValidationError as DRFValidationError

from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import (
    HttpResponseBadRequest,
    HttpResponseForbidden,
    HttpResponseNotFound,
    HttpResponseServerError,
)


@dataclasses.dataclass
class Error:
    code: str
    message: str
    status_code: Optional[int] = 500


@dataclasses.dataclass
class Errors:
    UNAUTHORIZED = Error("UNAUTHORIZED", "Unauthorized", status.HTTP_401_UNAUTHORIZED)
    BAD_REQUEST = Error("BAD_REQUEST", "Bad request", HttpResponseBadRequest.status_code)
    PERMISSION_DENIED = Error("PERMISSION_DENIED", "Permission denied", HttpResponseForbidden.status_code)
    NOT_FOUND = Error("NOT_FOUND", "Not found", HttpResponseNotFound.status_code)
    INTERNAL_SERVER_ERROR = Error(
        "INTERNAL_SERVER_ERROR", "An unexpected error occurred", HttpResponseServerError.status_code
    )
    TOO_MANY_REQUESTS = Error("TOO_MANY_REQUESTS", "Too many requests", status.HTTP_429_TOO_MANY_REQUESTS)
    SERVICE_UNAVAILABLE = Error("SERVICE_UNAVAILABLE", "Service Unavailable", status.HTTP_503_SERVICE_UNAVAILABLE)


EXCEPTION_ERROR_MAP = {
    DjangoValidationError: Errors.BAD_REQUEST,
    DRFValidationError: Errors.BAD_REQUEST,
    ObjectDoesNotExist: Errors.NOT_FOUND,
    PermissionDenied: Errors.PERMISSION_DENIED,
    PermissionError: Errors.PERMISSION_DENIED,
    JWTPermissionDenied: Errors.UNAUTHORIZED,
    APIError: Errors.SERVICE_UNAVAILABLE,
}

EXCEPTION_ERROR_TEXT_MAP = {
    "Must be logged in to access this mutation.": Errors.UNAUTHORIZED,
}
