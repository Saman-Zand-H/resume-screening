class AcademyClientException(Exception):
    """Base exception for AcademyClient errors."""

    pass


class AcademyUnauthorizedException(AcademyClientException):
    """Raised for unauthorized access to the API."""

    pass


class AcademyRequestException(AcademyClientException):
    """Raised for other request errors."""

    pass
