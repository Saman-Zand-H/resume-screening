import traceback
from dataclasses import asdict
from typing import Optional

from graphql import GraphQLError as BaseGraphQLError
from rest_framework.exceptions import ValidationError as DRFValidationError

from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError

from .errors import Error, Errors

EXCEPTION_SERIALIZERS = {
    DjangoValidationError: lambda e: dict(fields=getattr(e, "message_dict", None)),
    DRFValidationError: lambda e: dict(message=str(e.detail[0])),
}


class GraphQLError(BaseGraphQLError):
    error: Optional[Error] = None

    def __init__(
        self,
        error: Error = None,
        *,
        message: str = None,
        extensions: Optional[dict] = None,
        exception: Exception = None,
    ):
        self.error = error or self.error or Errors.INTERNAL_SERVER_ERROR

        if extensions is None:
            extensions = {}

        extensions.update(asdict(self.error))

        if settings.DEBUG and exception:
            extensions.update({"details": str(exception)})
            print("".join(traceback.TracebackException.from_exception(exception).format()))

        if (exception_class := type(exception)) in EXCEPTION_SERIALIZERS:
            extensions.update(EXCEPTION_SERIALIZERS[exception_class](exception))
        message = message or extensions.get("message")
        extensions.pop("message", None)
        super().__init__(message=message or self.error.message, extensions=extensions)

    def asdict(self):
        return {
            "error": self.error,
            "message": self.message,
            "extensions": self.extensions,
        }


class GraphQLErrorBaseException(GraphQLError):
    def __init__(self, message: str = None, *args, **kwargs):
        super().__init__(message=message, *args, **kwargs)


class GraphQLErrorBadRequest(GraphQLErrorBaseException):
    error = Errors.BAD_REQUEST
