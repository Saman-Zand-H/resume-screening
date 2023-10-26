import contextlib

from phonenumber_field.modelfields import PhoneNumberField

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _


class LinkedInUsernameValidator(RegexValidator):
    regex = r"^(https:\/\/)?(www\.)?linkedin\.com\/in\/[A-Za-z0-9_.-]+\/?$"
    message = _("Enter a valid LinkedIn username. This value may contain only letters, numbers, and _.")


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
