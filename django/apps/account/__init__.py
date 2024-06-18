import copy
import functools
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


with warnings.catch_warnings():
    warnings.simplefilter("ignore", DeprecationWarning)
    import fitz  # noqa: F401
