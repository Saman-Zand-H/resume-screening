import contextlib
import re

from phonenumber_field.modelfields import PhoneNumberField

from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator, RegexValidator
from django.utils.regex_helper import _lazy_re_compile
from django.utils.translation import gettext_lazy as _

from .constants import EXTENDED_EMAIL_BLOCKLIST


class LinkedInUsernameValidator(RegexValidator):
    regex = r"^(https:\/\/)?(www\.)?linkedin\.com\/in\/[A-Za-z0-9_-]+\/?$"
    message = _("Enter a valid LinkedIn username url eg: https://www.linkedin.com/in/username")


class WhatsAppValidator(RegexValidator):
    regex = r"^(https:\/\/)?(www\.)?wa\.me\/[0-9]+\/?$"
    message = _("Enter a valid WhatsApp username eg: https://wa.me/1234567890 or +1234567890")

    def __call__(self, value):
        with contextlib.suppress(ValidationError):
            PhoneNumberField().run_validators(value)
            return
        return super().__call__(value)


class NameValidator(RegexValidator):
    regex = r"^[A-Za-z\s]*$"
    message = _("Enter a valid name. This value may contain only letters and spaces.")


class NoTagEmailValidator(EmailValidator):
    user_regex = _lazy_re_compile(
        # dot-atom
        r"(^[-!#$%&'*/=?^_`{}|~0-9A-Z]+(\.[-!#$%&'*/=?^_`{}|~0-9A-Z]+)*\Z"
        # quoted-string
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
