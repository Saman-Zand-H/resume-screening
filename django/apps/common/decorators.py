from functools import partial, wraps

from django_ratelimit import ALL, UNSAFE
from django_ratelimit.core import is_ratelimited
from graphene_django_cud.mutations.core import DjangoCudBase
from graphql import GraphQLResolveInfo
from graphql_jwt.decorators import login_required as jwt_login_required

from common.exceptions import GraphQLErrorTooManyRequests
from django.utils.translation import gettext as _

from .utils import get_mutate_overrider_mixin


class RateLimit:
    @classmethod
    def _apply_ratelimit(cls, fn, group=None, key=None, rate=None, method=ALL, block=True):
        """Applies rate limiting to the given function."""

        @wraps(fn)
        def wrapped(*args, **kwargs):
            info = next((arg for arg in args if isinstance(arg, GraphQLResolveInfo)), None)
            if not info:
                return fn(*args, **kwargs)

            request = info.context
            request.limited = is_ratelimited(
                request=request,
                group=group,
                fn=fn,
                key=key,
                rate=rate,
                method=method,
                increment=True,
            ) or getattr(request, "limited", False)

            if request.limited and block:
                raise GraphQLErrorTooManyRequests(_("Too many requests"))

            return fn(*args, **kwargs)

        return wrapped

    @classmethod
    def __call__(cls, **rate_kwargs):
        """Decorator to apply rate limiting on functions or classes."""

        def decorator(fn):
            if isinstance(fn, type):
                if issubclass(fn, DjangoCudBase):
                    fn.before_mutate = cls._apply_ratelimit(fn.before_mutate, **rate_kwargs)
                else:
                    fn = get_mutate_overrider_mixin(fn, cls.__name__, cls._apply_ratelimit(fn.mutate, **rate_kwargs))
            else:
                fn = cls._apply_ratelimit(fn, **rate_kwargs)
            return fn

        return decorator


ratelimit = RateLimit()
ratelimit.ALL = ALL
ratelimit.UNSAFE = UNSAFE


class LoginRequired:
    @classmethod
    def __call__(cls, fn):
        if isinstance(fn, type):
            if issubclass(fn, DjangoCudBase):
                fn.before_mutate = jwt_login_required(fn.before_mutate)
            else:
                fn = get_mutate_overrider_mixin(fn, cls.__name__, jwt_login_required(fn.mutate))
        else:
            fn = jwt_login_required(fn)
        return fn


login_required = LoginRequired()
