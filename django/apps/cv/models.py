import os
from urllib.parse import urlparse

import pdfkit
from account.models import Contact, User, WorkExperience
from common.choices import LANGUAGES
from common.validators import DOCUMENT_FILE_SIZE_VALIDATOR, FileExtensionValidator
from config.settings.constants import Environment
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
        static_base_url = "http://localhost:8000"
        if not (settings.SITE_DOMAIN and "localhost" not in settings.SITE_DOMAIN):
            static_base_url = f"https://{urlparse(settings.SITE_DOMAIN).netloc}"
        return template.replace(
            settings.STATIC_URL,
            f"{static_base_url}{settings.STATIC_URL}",
        )

    def render_pdf(self, context: dict) -> bytes:
        template = self.render(context)
        options = {
            "margin-top": "0",
            "margin-right": "0",
            "margin-bottom": "0",
            "margin-left": "0",
            "zoom": 1.0,
            "enable-local-file-access": "",
            "encoding": "UTF-8",
        }
        pdf_bytes: bytes = pdfkit.from_string(
            template,
            output_path=False,
            options=options,
        )
        return pdf_bytes

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
        educations = user.educations.all()
        work_experiences = user.workexperiences.filter(
            status__in=[
                WorkExperience.Status.VERIFIED,
                WorkExperience.Status.SELF_VERIFIED,
            ]
        )
        about_me = "default"
        languages = [user.profile.native_language, *(user.profile.fluent_languages or [])]
        languages_dict = dict(LANGUAGES)
        social_contacts = user.contacts.filter(
            type__in=[
                Contact.Type.LINKEDIN,
                Contact.Type.WHATSAPP,
                Contact.Type.WEBSITE,
            ],
        )
        certifications = user.certificateandlicenses.all()
        phone = phone_qs.first().value if (phone_qs := user.contacts.filter(type=Contact.Type.PHONE)).exists() else None
        skills = user.skills.all()

        return {
            "user": user,
            "educations": educations,
            "work_experiences": work_experiences,
            "about_me": about_me,
            "phone": phone,
            "certifications": certifications,
            "languages": [languages_dict.get(lang) for lang in languages],
            "social_contacts": social_contacts,
            "skills": skills,
            "now": timezone.now(),
        }

    @classmethod
    def from_user(cls, user, template: CVTemplate = None):
        pdf = cls.generate(user, template)
        file = ContentFile(pdf, name=f"cpj_cv_{user.first_name}_{user.last_name}.pdf")
        return cls.objects.update_or_create(user=user, defaults={"file": file})

    class Meta:
        verbose_name = _("CV File")
        verbose_name_plural = _("CV Files")
