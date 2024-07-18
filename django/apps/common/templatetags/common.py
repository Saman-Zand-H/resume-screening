from account.constants import SUPPORT_EMAIL

from django import template

register = template.Library()


@register.simple_tag
def email_variables(name):
    return {
        "support_email": SUPPORT_EMAIL,
    }[name]
