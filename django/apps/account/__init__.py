import copy
import functools
import re
import warnings

from graphql_jwt import decorators


def __monkeypatch_graphql_jwt_datetime_func__():
    def disable_warnings(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            import warnings

            warnings.filterwarnings(action="ignore", message=r"datetime.datetime.utcnow")

            return f(*args, **kwargs)

        return wrapper

    decorators.refresh_expiration = disable_warnings(copy.deepcopy(decorators.refresh_expiration))
    decorators.jwt_cookie = disable_warnings(copy.deepcopy(decorators.jwt_cookie))


__monkeypatch_graphql_jwt_datetime_func__()


class WarningFilter:
    def __init__(self):
        self.patterns = [
            r"builtin type SwigPyPacked has no __module__ attribute",
            r"builtin type SwigPyObject has no __module__ attribute",
            r"builtin type swigvarlink has no __module__ attribute",
        ]

    def filter(self, message):
        for pattern in self.patterns:
            if re.search(pattern, message):
                return True
        return False


class IgnoreSpecificWarnings:
    def __init__(self):
        self.warning_filter = WarningFilter()

    def __call__(self, message, category, filename, lineno, file=None, line=None):
        if self.warning_filter.filter(str(message)):
            return

        warnings.showwarning(message, category, filename, lineno, file, line)


warnings.showwarning = IgnoreSpecificWarnings()
