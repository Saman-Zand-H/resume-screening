from django.db import models
from django.utils.translation import gettext_lazy as _


class DocumentStatus(models.TextChoices):
    DRAFTED = "drafted", _("Drafted")
    SUBMITTED = "submitted", _("Submitted")
    REJECTED = "rejected", _("Rejected")
    VERIFIED = "verified", _("Verified")
    SELF_VERIFIED = "self_verified", _("Self Verified")
