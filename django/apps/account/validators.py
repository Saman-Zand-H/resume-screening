from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _


class LinkedInUsernameValidator(RegexValidator):
    regex = r"^(https:\/\/)?(www\.)?linkedin\.com\/in\/[A-Za-z0-9_.-]+\/?$"
    message = _("Enter a valid LinkedIn username. This value may contain only letters, numbers, and _.")


class WhatsAppValidator(RegexValidator):
    regex = r"^(https:\/\/)?(www\.)?wa\.me\/[0-9]+\/?$"
    message = _("Enter a valid WhatsApp username. This value may contain only numbers.")
