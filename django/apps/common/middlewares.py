import logging
from django.views.debug import ExceptionReporter

from .exceptions import GraphQLError
from .utils import map_exception_to_error


logger = logging.getLogger("graphql.error")


class ErrorHandlingMiddleware:
    def on_error(self, request, exc_type, exc_value, tb):
        reporter = ExceptionReporter(request, exc_type, exc_value, tb, is_email=False)
        html = reporter.get_traceback_html()
        logger.error("GraphQL Execution Error", extra={"html_error": html})

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
                error = map_exception_to_error(e.__class__, str(e))
                kwargs.update({"error": error})
            kwargs.update({"exception": e})

            request = info.context
            exc_type, exc_value, tb = type(e), e, e.__traceback__
            self.on_error(request, exc_type, exc_value, tb)

            raise base_exception(**kwargs)
