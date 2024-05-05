import os

import weasyprint
from common.validators import DOCUMENT_FILE_SIZE_VALIDATOR, FileExtensionValidator
from flex_blob.models import FileModel

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.template.loader import TemplateDoesNotExist, get_template
from django.utils.translation import gettext_lazy as _

from .constants import TEMPLATE_VALID_EXTENSIONS


class CVTemplate(models.Model):
    title = models.CharField(max_length=255, verbose_name=_("Title"), unique=True)
    path = models.CharField(max_length=255, verbose_name=_("Path"), unique=True)
    is_active = models.BooleanField(default=True, verbose_name=_("Is active"))

    def clean(self):
        if os.path.splitext(self.path)[1] not in TEMPLATE_VALID_EXTENSIONS:
            raise ValidationError(
                _("Invalid template extension. Valid extensions are: %(valid_extensions)s")
                % {"valid_extensions": ", ".join(TEMPLATE_VALID_EXTENSIONS)}
            )

        try:
            self.get_template_object()
        except TemplateDoesNotExist:
            raise ValidationError(_("Template does not exist"))

    def get_template_object(self):
        return get_template(self.path)

    def render(self, context: dict) -> str:
        return self.get_template_object().render(context)

    def render_pdf(self, context: dict, target_file_name: str = None) -> bytes:
        return weasyprint.HTML(string=self.render(context)).write_pdf(target_file_name)

    def __str__(self):
        return f"{self.title}: {self.path}"

    class Meta:
        verbose_name = _("CV Template")
        verbose_name_plural = _("CV Templates")


class CVFile(FileModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cv",
        verbose_name=_("User"),
    )

    def __str__(self):
        return f"{self.user}: {self.file.name}"

    def get_upload_path(self, filename):
        return f"{self.user.pk}/cv/{filename}"

    def get_validators(self):
        return [
            FileExtensionValidator(["pdf"]),
            DOCUMENT_FILE_SIZE_VALIDATOR,
        ]

    def check_auth(self, request):
        return True

    class Meta:
        verbose_name = _("CV File")
        verbose_name_plural = _("CV Files")
