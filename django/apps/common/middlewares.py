from django.core.exceptions import ValidationError
from django.conf import settings

from .exceptions import BaseGraphQLError
from .errors import ERROR_MAP, Errors


class ErrorHandlingMiddleware:
    def resolve(self, next, root, info, **args):
        try:
            return next(root, info, **args)
        except Exception as e:
            error = Errors.INTERNAL_SERVER_ERROR
            for k, v in ERROR_MAP.items():
                if isinstance(e, k):
                    error = v
                    break

            extensions = {}
            if settings.DEBUG:
                extensions.update({"details": str(e)})
            if isinstance(e, ValidationError):
                extensions.update({"fields": getattr(e, "message_dict", None)})
            raise BaseGraphQLError(error=error, extensions=extensions)
