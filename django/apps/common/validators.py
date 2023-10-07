from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _


@deconstructible
class ValidateFileSize:
    max = None

    def __init__(self, max):
        self.max = max

    def __call__(self, value):
        if value.size > self.max * 1024 * 1024:
            raise ValidationError(code="max_file_size", message=_(f"You cannot upload file more than {self.max}Mb"))


IMAGE_FILE_SIZE_VALIDATOR = ValidateFileSize(max=3)
DOCUMENT_FILE_SIZE_VALIDATOR = ValidateFileSize(max=5)

DOCUMENT_FILE_EXTENSION_VALIDATOR = FileExtensionValidator(
    allowed_extensions=["pdf", "doc", "docx", "jpg", "jpeg", "png"]
)
