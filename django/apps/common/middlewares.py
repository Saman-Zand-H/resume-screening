import traceback

from sentry_sdk import capture_exception, get_current_scope

from common.logging import get_logger
from django.conf import settings
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin
from django.views.debug import ExceptionReporter

from .errors import Errors
from .exceptions import GraphQLError
from .utils import map_exception_to_error

graphql_logger = get_logger("graphql.error")


class GrapheneErrorHandlingMiddleware:
    def on_error(self, request, exc_type, exc_value, tb, error_kwargs):
        if settings.DEBUG:
            graphql_logger.error(
                "".join(traceback.TracebackException.from_exception(exc_value).format()),
                extra={"sentry_ignore": True},
            )

        if error_kwargs.get("error") is not Errors.INTERNAL_SERVER_ERROR:
            return

        scope = get_current_scope()
        scope.add_attachment(
            bytes=ExceptionReporter(request, exc_type, exc_value, tb, is_email=False)
            .get_traceback_html()
            .encode("utf-8"),
            filename=f"{exc_type.__name__}_{timezone.now().strftime('%Y-%m-%d-%H-%M-%S-%f')}",
            content_type="text/html",
        )
        capture_exception(exc_value)

    def resolve(self, next_resolver, root, info, **args):
        try:
            return next_resolver(root, info, **args)
        except Exception as e:
            base_exception = GraphQLError
            kwargs = {}

            if isinstance(e, GraphQLError):
                base_exception = e.__class__
                kwargs.update(e.asdict())
            else:
                kwargs.update({"error": map_exception_to_error(e.__class__, str(e))})
            kwargs.update({"exception": e})

            self.on_error(info.context, type(e), e, e.__traceback__, kwargs)

            raise base_exception(**kwargs)


class GrapheneDisableIntrospectionMiddleware:
    def resolve(self, next, root, info, **kwargs):
        if info.field_name.lower() in ["__schema", "__introspection"]:
            raise GraphQLError(Errors.PERMISSION_DENIED)
        return next(root, info, **kwargs)


class DjangoErrorHandlingMiddleware(MiddlewareMixin):
    def process_exception(self, request, exception):
        scope = get_current_scope()
        scope.add_attachment(
            bytes=ExceptionReporter(request, type(exception), exception, exception.__traceback__, is_email=False)
            .get_traceback_html()
            .encode("utf-8"),
            filename=f"{type(exception).__name__}_{timezone.now().strftime('%Y-%m-%d-%H-%M-%S-%f')}",
            content_type="text/html",
        )
