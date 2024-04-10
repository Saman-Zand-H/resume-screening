import os

import weasyprint

from django.core.exceptions import ValidationError
from django.db import models
from django.template.loader import TemplateDoesNotExist, get_template
from django.utils.translation import gettext_lazy as _

from .constants import TEMPLATE_VALID_EXTENSIONS
from .managers import CVContextManager
from .utils import get_template_variables


class CVRequiredContext(models.Model):
    title = models.CharField(max_length=255, verbose_name=_("Title"))
    value = models.CharField(max_length=255, verbose_name=_("Value"))

    objects = CVContextManager()

    def __str__(self):
        return f"{self.title}: {{ {self.value} }}"

    class Meta:
        verbose_name = _("CV Context")
        verbose_name_plural = _("CV Contexts")


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
            template_object = self.get_template_object()
        except TemplateDoesNotExist:
            raise ValidationError(_("Template does not exist"))

        required_contexts: models.QuerySet[CVRequiredContext] = CVRequiredContext.objects.all()
        used_variables = get_template_variables(template_object.template)
        if not set(required_contexts.values_list("value", flat=True)).issubset(used_variables):
            raise ValidationError(
                _("Template does not use all required context variables. Missing variables: %(missing_vars)s")
                % {"missing_vars": ", ".join(set(required_contexts.values_list("value", flat=True)) - used_variables)}
            )

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
