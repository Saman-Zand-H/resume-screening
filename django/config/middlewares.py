import logging
from django.utils.deprecation import MiddlewareMixin
from django.views.debug import ExceptionReporter


logger = logging.getLogger("django.error")


class DjangoErrorHandlingMiddleware(MiddlewareMixin):
    def process_exception(self, request, exception):
        reporter = ExceptionReporter(request, type(exception), exception, exception.__traceback__, is_email=False)
        html = reporter.get_traceback_html()
        logger.error("Django Server Error", extra={"html_error": html})
