from functools import partial, wraps

from django_ratelimit import ALL, UNSAFE
from django_ratelimit.core import is_ratelimited
from graphql import GraphQLResolveInfo

from common.exceptions import GraphQLErrorTooManyRequests
from django.utils.translation import gettext as _

from .mixins import MutateDecoratorMixin


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
                return type(
                    fn.__name__,
                    (MutateDecoratorMixin, fn),
                    {MutateDecoratorMixin.decorator.fget.__name__: partial(cls._apply_ratelimit, **rate_kwargs)},
                )
            return cls._apply_ratelimit(fn, **rate_kwargs)

        return decorator


ratelimit = RateLimit()
ratelimit.ALL = ALL
ratelimit.UNSAFE = UNSAFE
