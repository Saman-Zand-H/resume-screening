import contextlib
from operator import call

from account.constants import SUPPORT_EMAIL

from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def call_method(obj, method_name, *args, **kwargs):
    with contextlib.suppress(AttributeError):
        return call(getattr(obj, method_name), *args, **kwargs)

    return mark_safe("&mdash;")


@register.simple_tag
def email_variables(name):
    return {
        "support_email": SUPPORT_EMAIL,
    }[name]
