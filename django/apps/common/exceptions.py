import traceback
from dataclasses import asdict
from functools import wraps
from typing import Callable, Dict, List, Optional

from graphql import GraphQLError as BaseGraphQLError
from rest_framework.exceptions import ValidationError as DRFValidationError

from common.logging import get_logger
from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError

from .errors import Error, Errors
from .utils import deserialize_field_error

logger = get_logger()


def error_dict_deserializer(func: Callable[[DjangoValidationError], Dict[str, List[str]]]):
    @wraps(func)
    def wrapper(e: DjangoValidationError):
        error_dict = func(e)

        return {
            field_name: [deserialize_field_error(error) for error in errors]
            for field_name, errors in (error_dict.get("message") or error_dict.get("fields")).items()
        }

    return wrapper


@error_dict_deserializer
def django_validation_error_serializer(e: DjangoValidationError):
    if message_dict := getattr(e, "message_dict", None):
        return dict(fields=message_dict)

    return dict(message=e.message, fields={})


EXCEPTION_SERIALIZERS = {
    DjangoValidationError: django_validation_error_serializer,
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
            logger.error("".join(traceback.TracebackException.from_exception(exception).format()))

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
