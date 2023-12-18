import dataclasses
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from graphql_jwt.exceptions import PermissionDenied as JWTPermissionDenied


@dataclasses.dataclass
class Error:
    code: str
    message: str


@dataclasses.dataclass
class Errors:
    VALIDATION_ERROR = Error("VALIDATION_ERROR", "Validation Error")
    NOT_FOUND = Error("NOT_FOUND", "Not found")
    PERMISSION_DENIED = Error("PERMISSION_DENIED", "Permission denied")
    AUTHENTICATION_ERROR = Error("AUTHENTICATION_ERROR", "Authentication error")
    INTERNAL_SERVER_ERROR = Error("INTERNAL_SERVER_ERROR", "An unexpected error occurred")


ERROR_MAP = {
    DjangoValidationError: Errors.VALIDATION_ERROR,
    ObjectDoesNotExist: Errors.NOT_FOUND,
    PermissionDenied: Errors.PERMISSION_DENIED,
    JWTPermissionDenied: Errors.PERMISSION_DENIED,
}
