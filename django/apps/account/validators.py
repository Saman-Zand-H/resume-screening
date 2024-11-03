import re
from typing import List

from config.settings.constants import Environment
from django.conf import settings

from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator, RegexValidator
from django.utils.regex_helper import _lazy_re_compile
from django.utils.translation import gettext_lazy as _

from .constants import EXTENDED_EMAIL_BLOCKLIST, EmailConstants
from .utils import is_env


class LinkedInUsernameValidator(RegexValidator):
    regex = r"^(https:\/\/)?(www\.)?linkedin\.com\/in\/[A-Za-z0-9_-]+\/?$"
    message = _("Enter a valid LinkedIn username url eg: https://www.linkedin.com/in/username")


class NameValidator(RegexValidator):
    regex = r"^[A-Za-z\s]*$"
    message = _("Enter a valid name. This value may contain only letters and spaces.")


class NoTagEmailValidator(EmailValidator):
    if not is_env(Environment.LOCAL, Environment.DEVELOPMENT):
        user_regex = _lazy_re_compile(
            r"(^[-!#$%&'*/=?^_`{}|~0-9A-Z]+(\.[-!#$%&'*+/=?^_`{}|~0-9A-Z]+)*\Z"
            r'|^"([\001-\010\013\014\016-\037!#-\[\]-\177]|\\[\001-\011\013\014\016-\177])'
            r'*"\Z)',
            re.IGNORECASE,
        )


class BlocklistEmailDomainValidator(EmailValidator):
    def __call__(self, value):
        super().__call__(value)
        domain = value.split("@")[-1]
        if domain in EXTENDED_EMAIL_BLOCKLIST:
            raise ValidationError(_("This domain is blocked. Please use a different email address."))


class EmailCallbackURLValidator:
    def __init__(self, values: List[str] = None):
        self.values = values or settings.VALID_EMAIL_CALLBACK_URLS

    def __call__(self, value):
        domain = (".".join(value.split(".")[-2:])).split("/", 1)[0]
        if not settings.DEBUG and all(domain != val for val in self.values):
            raise ValidationError({EmailConstants.CALLBACK_URL_VARIABLE: _("This URL is not allowed.")})
