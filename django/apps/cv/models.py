import os

import pdfkit
from account.models import Contact, User
from common.validators import DOCUMENT_FILE_SIZE_VALIDATOR, FileExtensionValidator
from flex_blob.models import FileModel
from model_utils.models import TimeStampedModel

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db import models
from django.template.loader import TemplateDoesNotExist, get_template, render_to_string
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .constants import TEMPLATE_VALID_EXTENSIONS
from .utils import (
    extract_generated_resume_info,
    get_resume_info_input,
    get_static_base_url,
    merge_pdf_pages_to_single_page,
)


class CVTemplate(TimeStampedModel):
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
            get_template(self.path)
        except TemplateDoesNotExist:
            raise ValidationError(_("Template does not exist"))

    def render(self, context: dict) -> str:
        template = render_to_string(self.path, context)

        return template.replace(
            settings.STATIC_URL,
            f"{get_static_base_url()}{settings.STATIC_URL}",
        )

    def render_pdf(self, context: dict, **options) -> bytes:
        template = self.render(context)
        options = {
            "margin-top": "0",
            "margin-right": "0",
            "margin-bottom": "0",
            "margin-left": "0",
            "zoom": 1.0,
            "enable-local-file-access": "",
            "encoding": "UTF-8",
            "disable-smart-shrinking": "",
            "dpi": 500,
            **options,
        }

        pdf_bytes: bytes = pdfkit.from_string(
            template,
            output_path=False,
            options=options,
        )
        return merge_pdf_pages_to_single_page(pdf_bytes)

    def __str__(self):
        return f"{self.title}: {self.path}"

    class Meta:
        verbose_name = _("CV Template")
        verbose_name_plural = _("CV Templates")


class GeneratedCV(FileModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cv",
        verbose_name=_("User"),
    )
    input_json = models.JSONField(verbose_name=_("Input JSON"), blank=True, null=True)
    work_experiences = models.JSONField(verbose_name=_("Work Experiences"), blank=True, null=True)
    educations = models.JSONField(verbose_name=_("Educations"), blank=True, null=True)
    certifications = models.JSONField(verbose_name=_("Certifications"), blank=True, null=True)
    additional_sections = models.JSONField(verbose_name=_("Additional Sections"), blank=True, null=True)

    @classmethod
    def get_resume_info(cls, user: User, template: CVTemplate = None):
        if not template:
            template = CVTemplate.objects.latest("created")

        if (instance := cls.object.filter(user=user, template=template)) and instance.input_json == (
            input_json := get_resume_info_input(user)
        ):
            return {
                "work_experiences": instance.work_experiences,
                "educations": instance.educations,
                "certifications": instance.certifications,
                "additional_sections": instance.additional_sections,
            }

        instance.input_json = input_json
        instance.save()
        resume_info = extract_generated_resume_info(user)
        return resume_info

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
        return request.user == self.user

    @classmethod
    def generate(cls, user: User, template: CVTemplate = None):
        if not template:
            template = CVTemplate.objects.latest("created")

        context = cls.get_user_context(user)
        return template.render_pdf(context)

    @classmethod
    def get_user_context(cls, user: User):
        profile = user.profile
        contacts = Contact.objects.filter(
            contactable__profile__user=user,
            type__in=[
                Contact.Type.LINKEDIN,
                Contact.Type.WHATSAPP,
                Contact.Type.WEBSITE,
                Contact.Type.PHONE,
            ],
        )
        skills = profile.skills.all()
        asssistant_data = cls.get_resume_info(user)

        return {
            "user": user,
            "contacts": contacts,
            "skills": skills,
            "now": timezone.now(),
            **asssistant_data,
        }

    @classmethod
    def from_user(cls, user, template: CVTemplate = None):
        pdf = cls.generate(user, template)
        file = ContentFile(pdf, name=f"cpj_cv_{user.first_name.lower()}_{user.last_name.lower()}.pdf")
        return cls.objects.update_or_create(user=user, defaults={"file": file})

    class Meta:
        verbose_name = _("CV File")
        verbose_name_plural = _("CV Files")
