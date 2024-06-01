import logging

from django.utils.deprecation import MiddlewareMixin
from django.views.debug import ExceptionReporter

from .errors import Errors
from .exceptions import GraphQLError
from .utils import map_exception_to_error

graphql_logger = logging.getLogger("graphql.error")
django_logger = logging.getLogger("django.error")


class GrapheneErrorHandlingMiddleware:
    def on_error(self, request, exc_type, exc_value, tb):
        reporter = ExceptionReporter(request, exc_type, exc_value, tb, is_email=False)
        html = reporter.get_traceback_html()
        graphql_logger.error("GraphQL Execution Error", extra={"html_error": html})

    def resolve(self, next_resolver, root, info, **args):
        try:
            return next_resolver(root, info, **args)
        except Exception as e:
            base_exception = GraphQLError
            kwargs = {}

            error = map_exception_to_error(e.__class__, str(e))
            if isinstance(e, GraphQLError):
                base_exception = e.__class__
                kwargs.update(e.asdict())
            else:
                kwargs.update({"error": error})
            kwargs.update({"exception": e})

            if error is Errors.INTERNAL_SERVER_ERROR:
                self.on_error(info.context, type(e), e, e.__traceback__)

            raise base_exception(**kwargs)


class DjangoErrorHandlingMiddleware(MiddlewareMixin):
    def process_exception(self, request, exception):
        reporter = ExceptionReporter(request, type(exception), exception, exception.__traceback__, is_email=False)
        html = reporter.get_traceback_html()
        django_logger.error("Django Server Error", extra={"html_error": html})
