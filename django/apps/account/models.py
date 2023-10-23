from cities_light.models import City
from colorfield.fields import ColorField
from common.models import Field, Job, University
from common.validators import (
    DOCUMENT_FILE_EXTENSION_VALIDATOR,
    DOCUMENT_FILE_SIZE_VALIDATOR,
    IMAGE_FILE_SIZE_VALIDATOR,
)
from phonenumber_field.modelfields import PhoneNumberField

from django.apps import apps
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import UserManager as BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
import re


def full_body_image_path(instance, filename):
    return f"profile/{instance.user.id}/full_body_image/{filename}"


def get_education_verification_path(path, instance, filename):
    return f"profile/{instance.education.user.id}/education_verification/{path}/{filename}"


def ices_document_path(instance, filename):
    return get_education_verification_path("ices", instance, filename)


def citizen_document_path(instance, filename):
    return get_education_verification_path("citizen", instance, filename)


def degree_file_path(instance, filename):
    return get_education_verification_path("degree", instance, filename)


class UserManager(BaseUserManager):
    def create_user(self, **kwargs):
        kwargs.setdefault("username", kwargs.get(self.model.USERNAME_FIELD))
        return super().create_user(**kwargs)

    def create_superuser(self, **kwargs):
        kwargs.setdefault("username", kwargs.get(self.model.USERNAME_FIELD))
        return super().create_superuser(**kwargs)


class User(AbstractUser):
    class Gender(models.TextChoices):
        MALE = "male", _("Male")
        FEMALE = "female", _("Female")
        NOT_KNOWN = "not_known", _("Not Known")
        NOT_APPLICABLE = "not_applicable", _("Not Applicable")

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    gender = models.CharField(
        max_length=50,
        choices=Gender.choices,
        verbose_name=_("Gender"),
        null=True,
        blank=True,
    )
    birth_date = models.DateField(verbose_name=_("Birth Date"), null=True, blank=True)
    phone = PhoneNumberField(verbose_name=_("Phone Number"), null=True, blank=True)

    objects = UserManager()


User._meta.get_field("email")._unique = True
User._meta.get_field("email").blank = False
User._meta.get_field("email").null = False
User._meta.get_field("username").blank = True
User._meta.get_field("username").null = True


class Profile(models.Model):
    class SkinColor(models.TextChoices):
        VERY_FAIR = "#FFDFC4", "Very Fair"
        FAIR = "#F0D5B1", "Fair"
        LIGHT = "#E5B897", "Light"
        LIGHT_MEDIUM = "#D9A377", "Light Medium"
        MEDIUM = "#C68642", "Medium"
        OLIVE = "#A86B33", "Olive"
        BROWN = "#8D5524", "Brown"
        DARK_BROWN = "#603913", "Dark Brown"
        VERY_DARK = "#3B260B", "Very Dark"
        DEEP = "#100C08", "Deep"

    class EyeColor(models.TextChoices):
        AMBER = "#FFBF00", "Amber"
        BLUE = "#5DADEC", "Blue"
        BROWN = "#6B4226", "Brown"
        GRAY = "#BEBEBE", "Gray"
        GREEN = "#1CAC78", "Green"
        HAZEL = "#8E7618", "Hazel"
        RED = "#FF4500", "Red"
        VIOLET = "#8F00FF", "Violet"

    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name=_("User"))
    height = models.IntegerField(null=True, blank=True)
    weight = models.IntegerField(null=True, blank=True)
    skin_color = ColorField(choices=SkinColor.choices, null=True, blank=True, verbose_name=_("Skin Color"))
    hair_color = ColorField(null=True, blank=True, verbose_name=_("Hair Color"))
    eye_color = ColorField(choices=EyeColor.choices, null=True, blank=True, verbose_name=_("Eye Color"))
    full_body_image = models.ImageField(
        upload_to=full_body_image_path,
        validators=[IMAGE_FILE_SIZE_VALIDATOR],
        null=True,
        blank=True,
        verbose_name=_("Full Body Image"),
    )
    job = models.ManyToManyField(Job, verbose_name=_("Job"), blank=True)
    city = models.ForeignKey(City, on_delete=models.SET_NULL, verbose_name=_("City"), null=True, blank=True)

    class Meta:
        verbose_name = _("User Profile")
        verbose_name_plural = _("User Profiles")

    def __str__(self):
        return self.user.email


class Contact(models.Model):
    class ContactType(models.TextChoices):
        WEBSITE = "website", _("Website")
        ADDRESS = "address", _("Address")
        LINKEDIN = "linkedin", _("LinkedIn")
        WHATSAPP = "whatsapp", _("WhatsApp")

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_("User"), related_name="contacts")
    type = models.CharField(
        max_length=50,
        choices=ContactType.choices,
        verbose_name=_("Type"),
        default=ContactType.WEBSITE.value,
    )
    value = models.CharField(max_length=255, verbose_name=_("Value"))

    class Meta:
        unique_together = ("user", "type")
        verbose_name = _("Contact")
        verbose_name_plural = _("Contacts")

    def __str__(self):
        return f"{self.user.email} - {self.type}: {self.value}"

    def full_clean(self, *args, **kwargs):
        super().full_clean(*args, **kwargs)
        cleaning_method = getattr(self, f"clean_{self.type}", None)
        if cleaning_method:
            cleaning_method()

    def clean_website(self):
        url_validator = URLValidator()
        try:
            url_validator(self.value)
        except ValidationError:
            raise ValidationError(_("Invalid website URL"))

    def clean_address(self):
        if len(self.value) < 5:
            raise ValidationError(_("Address is too short"))

    def clean_linkedin(self):
        linkedin_pattern = r"^https:\/\/([a-z]{2,3}\.)?linkedin\.com\/.*$"
        if not re.match(linkedin_pattern, self.value):
            raise ValidationError(_("Invalid LinkedIn profile URL"))

    def clean_whatsapp(self):
        # TODO: add validation
        pass


class Education(models.Model):
    class Degree(models.TextChoices):
        BACHELORS = "bachelors", _("Bachelors")
        MASTERS = "masters", _("Masters")
        PHD = "phd", _("PhD")
        ASSOCIATE = "associate", _("Associate")
        DIPLOMA = "diploma", _("Diploma")
        CERTIFICATE = "certificate", _("Certificate")

    class Status(models.TextChoices):
        VERIFIED = "verified", _("Verified")
        REJECTED = "rejected", _("Rejected")
        PENDING = "pending", _("Pending")
        DRAFT = "draft", _("Draft")

    class Method(models.TextChoices):
        IEE = (
            "iee",
            _("International Education Evaluation"),
        )
        COMMUNICATION = "communication", _("Communication")
        SELF_VERIFICATION = "self_verification", _("Self Verification")

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_("User"))
    field = models.ForeignKey(Field, on_delete=models.CASCADE, verbose_name=_("Field"))
    degree = models.CharField(max_length=50, choices=Degree.choices, verbose_name=_("Degree"))
    university = models.ForeignKey(University, on_delete=models.CASCADE, verbose_name=_("University"))
    start = models.DateField(verbose_name=_("Start Date"))
    end = models.DateField(verbose_name=_("End Date"), null=True, blank=True)
    status = models.CharField(
        max_length=50,
        choices=Status.choices,
        verbose_name=_("Status"),
        default=Status.PENDING.value,
    )
    method = models.CharField(max_length=50, choices=Method.choices, verbose_name=_("Verification Method"))
    is_verified = models.BooleanField(default=False, verbose_name=_("Is Verified"))
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At"),
    )
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    @staticmethod
    def get_method_models():
        _models = []
        for model in apps.get_models():
            if issubclass(model, EducationVerificationMethodAbstract):
                _models.append(model)
        return _models

    @staticmethod
    def get_method_choices():
        choices = dict.fromkeys(Education.Method.values)
        return choices | {
            method: model
            for method in choices.keys()
            for model in Education.get_method_models()
            if model.method == method
        }

    class Meta:
        verbose_name = _("Education")
        verbose_name_plural = _("Educations")

    def __str__(self):
        return f"{self.user.email} - {self.degree} in {self.field.name}"

    def save(self, *args, **kwargs):
        if self.method == self.Method.SELF_VERIFICATION:
            self.status = self.Status.VERIFIED.value
            self.is_verified = True
        super().save(*args, **kwargs)


class EducationVerificationMethodAbstract(models.Model):
    education = models.OneToOneField(
        Education,
        on_delete=models.CASCADE,
        verbose_name=_("Education"),
    )

    class Meta:
        abstract = True

    @classmethod
    def get_related_name(cls):
        return cls.education.field.related_query_name()

    def __str__(self):
        return f"{self.education.user.email} - {self.education.degree} Verification"


class IEEMethod(EducationVerificationMethodAbstract):
    class Evaluator(models.TextChoices):
        WES = "wes", _("World Education Services")
        IQAS = "iqas", _("International Qualifications Assessment Service")
        ICAS = "icas", _("International Credential Assessment Service of Canada")
        CES = "ces", _("Comparative Education Service")

    method = Education.Method.IEE

    ices_document = models.FileField(
        upload_to=ices_document_path,
        verbose_name=_("ICES Document"),
        validators=[DOCUMENT_FILE_EXTENSION_VALIDATOR, DOCUMENT_FILE_SIZE_VALIDATOR],
    )
    citizen_document = models.FileField(
        upload_to=citizen_document_path,
        verbose_name=_("Citizen Document"),
        validators=[DOCUMENT_FILE_EXTENSION_VALIDATOR, DOCUMENT_FILE_SIZE_VALIDATOR],
    )
    evaluator = models.CharField(
        max_length=50,
        choices=Evaluator.choices,
        verbose_name=_("Academic Credential Evaluator"),
    )

    class Meta:
        verbose_name = _("International Education Evaluation Method")
        verbose_name_plural = _("International Education Evaluation Methods")


class CommunicationMethod(EducationVerificationMethodAbstract):
    method = Education.Method.COMMUNICATION

    email = models.EmailField(verbose_name=_("Email"))
    department = models.CharField(max_length=255, verbose_name=_("Department"))
    person = models.CharField(max_length=255, verbose_name=_("Person"))
    degree_file = models.FileField(
        upload_to=degree_file_path,
        verbose_name=_("Degree File"),
        validators=[DOCUMENT_FILE_EXTENSION_VALIDATOR, DOCUMENT_FILE_SIZE_VALIDATOR],
    )

    class Meta:
        verbose_name = _("Communication Method")
        verbose_name_plural = _("Communication Methods")
