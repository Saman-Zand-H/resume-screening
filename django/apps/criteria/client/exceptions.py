class CriteriaClientException(Exception):
    """Base exception for CriteriaClient errors."""

    pass


class CriteriaUnauthorizedException(CriteriaClientException):
    """Raised for unauthorized access to the API."""

    pass


class CriteriaRequestException(CriteriaClientException):
    """Raised for other request errors."""

    pass
