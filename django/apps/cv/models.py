import contextlib
import json
import os
from typing import Tuple

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


class GeneratedCVContent(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cv_contents",
        verbose_name=_("User"),
    )
    work_experiences = models.JSONField(verbose_name=_("Work Experiences"), blank=True, null=True)
    educations = models.JSONField(verbose_name=_("Educations"), blank=True, null=True)
    certifications = models.JSONField(verbose_name=_("Certifications"), blank=True, null=True)
    additional_sections = models.JSONField(verbose_name=_("Additional Sections"), blank=True, null=True)
    about_me = models.TextField(verbose_name=_("About Me"), blank=True, null=True)
    headline = models.CharField(max_length=255, verbose_name=_("Headline"), blank=True, null=True)
    input_json = models.JSONField(verbose_name=_("Input JSON"), blank=True, null=True)

    @classmethod
    def get_resume_info(cls, user: User) -> Tuple[dict, bool]:
        input_json = get_resume_info_input(user)
        if (instance := cls.objects.filter(user=user).first()) and instance.input_json == json.loads(
            json.dumps(input_json)
        ):
            return {
                "work_experiences": instance.work_experiences,
                "educations": instance.educations,
                "certifications": instance.certifications,
                "additional_sections": instance.additional_sections,
                "about_me": instance.about_me,
                "headline": instance.headline,
            }, False

        if not instance:
            instance = cls.objects.create(user=user)

        resume_info = extract_generated_resume_info(user)
        cls.objects.filter(pk=instance.pk).update(
            work_experiences=resume_info.get("work_experiences"),
            educations=resume_info.get("educations"),
            certifications=resume_info.get("certifications"),
            input_json=input_json,
            additional_sections=resume_info.get("additional_sections"),
            about_me=resume_info.get("about_me"),
            headline=resume_info.get("headline"),
        )
        return resume_info, True

    def __str__(self):
        return f"{self.user}"

    class Meta:
        verbose_name = _("Generated CV Contents")
        verbose_name_plural = _("Generated CV Contents")


class GeneratedCV(TimeStampedModel, FileModel):
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
        if not request.user.is_authenticated:
            return False
        return (
            request.user == self.user
            or self.user.job_position_assignments.filter(
                job_position__organization__memberships__user=request.user
            ).exists()
        )

    @classmethod
    def get_user_context(cls, user: User) -> Tuple[dict, bool]:
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
        asssistant_data, generated = GeneratedCVContent.get_resume_info(user)

        return {
            "user": user,
            "contacts": contacts,
            "skills": skills,
            "now": timezone.now(),
            **asssistant_data,
        }, generated

    @classmethod
    def generate(cls, user: User, template: CVTemplate = None):
        if not template:
            template = CVTemplate.objects.latest("created")

        context, generated = cls.get_user_context(user)
        if not generated and cls.objects.filter(user=user).exists():
            with contextlib.suppress(GeneratedCV.DoesNotExist):
                return cls.objects.get(user=user).file.read()
        return template.render_pdf(context)

    @classmethod
    def from_user(cls, user, template: CVTemplate = None):
        pdf = cls.generate(user, template)
        file = ContentFile(pdf, name=f"cpj_cv_{user.first_name.lower()}_{user.last_name.lower()}.pdf")
        return cls.objects.update_or_create(user=user, defaults={"file": file})

    class Meta:
        verbose_name = _("CV File")
        verbose_name_plural = _("CV Files")
