import os
from typing import List

from django.core.validators import BaseValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from .fields import DynamicFileField


def dynamic_upload_to(instance, filename):
    return instance.get_upload_path(filename)


class FileModel(models.Model):
    file = DynamicFileField(
        upload_to=dynamic_upload_to,
        verbose_name=_("File"),
        db_index=True,
    )

    def check_auth(self, request=None):
        subclass_instance = self.get_subclass_instance()
        if subclass_instance and hasattr(subclass_instance, "check_auth"):
            return subclass_instance.check_auth(request)
        return False

    def get_upload_path(self, filename):
        return os.path.join("uploads", filename)

    def get_subclass_instance(self):
        for related_object in self._meta.related_objects:
            if hasattr(self, related_object.name):
                return getattr(self, related_object.name, None)
        return None

    def get_validators[T: BaseValidator](self) -> List[T]:
        return []

    def __str__(self):
        return self.file.name

    class Meta:
        verbose_name = _("Base File")
        verbose_name_plural = _("Base Files")
