from functools import wraps
from django.utils.translation import gettext as _
from django_ratelimit import ALL, UNSAFE
from django_ratelimit.core import is_ratelimited
from common.exceptions import GraphQLErrorTooManyRequests


def ratelimit(group=None, key=None, rate=None, method=ALL, block=False):
    def decorator(fn):
        @wraps(fn)
        def _wrapped(*args, **kwargs):
            root, info = args[-2], args[-1]
            request = info.context

            old_limited = getattr(request, "limited", False)

            ratelimited = is_ratelimited(
                request=request,
                group=group,
                fn=fn,
                key=key,
                rate=rate,
                method=method,
                increment=True,
            )
            request.limited = ratelimited or old_limited

            if ratelimited and block:
                raise GraphQLErrorTooManyRequests(_("Too many requests"))
            return fn(*args, **kwargs)

        return _wrapped

    return decorator


ratelimit.ALL = ALL
ratelimit.UNSAFE = UNSAFE
