from django.db.models import TextChoices
from django.utils.translation import gettext_lazy as _


class DataTypes(TextChoices):
    NUMERIC = "numeric", _("Numeric")
    STRING = "string", _("String")
    BOOLEAN = "boolean", _("Boolean")
    ENUM = "enum", _("Enum")
    # DATE = "data", _("Date")
    # DATETIME = "datetime", _("Date Time")
    # FILE = "file", _("File")
