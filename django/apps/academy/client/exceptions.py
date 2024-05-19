class AcademyClientException(Exception):
    """Base exception for AcademyClient errors."""

    status_code = None


class AcademyUnauthorizedException(AcademyClientException):
    """Raised for unauthorized access to the API."""

    pass


class AcademyRequestException(AcademyClientException):
    """Raised for other request errors."""


class AcademyNotFoundException(AcademyClientException):
    """Raised when the requested resource is not found."""

    status_code = 404


class AcademyBadRequestException(AcademyClientException):
    """Raised when the request is invalid."""

    status_code = 400


EXCEPTIONS = {
    400: AcademyBadRequestException,
    401: AcademyUnauthorizedException,
    404: AcademyNotFoundException,
}
