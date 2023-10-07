from colorfield.fields import ColorField
from common.models import Field, Job, University
from common.validators import (
    DOCUMENT_FILE_EXTENSION_VALIDATOR,
    DOCUMENT_FILE_SIZE_VALIDATOR,
    IMAGE_FILE_SIZE_VALIDATOR,
)

from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import UserManager as BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _


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
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()


User._meta.get_field("email")._unique = True
User._meta.get_field("email").blank = False
User._meta.get_field("email").null = False
User._meta.get_field("username").blank = True
User._meta.get_field("username").null = True


class UserProfile(models.Model):
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

    class Meta:
        verbose_name = _("User Profile")
        verbose_name_plural = _("User Profiles")

    def __str__(self):
        return self.user.email


class Education(models.Model):
    class DegreeChoices(models.TextChoices):
        BACHELORS = "bachelors", _("Bachelors")
        MASTERS = "masters", _("Masters")
        PHD = "phd", _("PhD")
        ASSOCIATE = "associate", _("Associate")
        DIPLOMA = "diploma", _("Diploma")
        CERTIFICATE = "certificate", _("Certificate")

    class StatusChoices(models.TextChoices):
        VERIFIED = "verified", _("Verified")
        REJECTED = "rejected", _("Rejected")
        PENDING = "pending", _("Pending")
        DRAFT = "draft", _("Draft")

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_("User"))
    field = models.ForeignKey(Field, on_delete=models.CASCADE, verbose_name=_("Field"))
    degree = models.CharField(max_length=50, choices=DegreeChoices.choices, verbose_name=_("Degree"))
    university = models.ForeignKey(University, on_delete=models.CASCADE, verbose_name=_("University"))
    start = models.DateField(verbose_name=_("Start Date"))
    end = models.DateField(verbose_name=_("End Date"), null=True, blank=True)
    status = models.CharField(
        max_length=50,
        choices=StatusChoices.choices,
        verbose_name=_("Status"),
        default=StatusChoices.PENDING,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At"),
    )
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    class Meta:
        verbose_name = _("Education")
        verbose_name_plural = _("Educations")

    def __str__(self):
        return f"{self.user.email} - {self.degree} in {self.field.name}"


class EducationVerification(models.Model):
    class MethodChoices(models.TextChoices):
        IEE = (
            "iee",
            _("International Education Evaluation"),
        )
        COMMUNICATION = "communication", _("Communication")
        SELF_VERIFICATION = "self_verification", _("Self Verification")

    education = models.ForeignKey(Education, on_delete=models.CASCADE, verbose_name=_("Education"))
    method = models.CharField(max_length=50, choices=MethodChoices.choices, verbose_name=_("Verification Method"))

    is_verified = models.BooleanField(default=False, verbose_name=_("Is Verified"))

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    class Meta:
        verbose_name = _("Education Verification")
        verbose_name_plural = _("Education Verifications")

    def __str__(self):
        return f"{self.education.user.email} - {self.education.degree} Verification"


class EducationVerificationMethodAbstract(models.Model):
    education_verification = models.OneToOneField(
        EducationVerification,
        on_delete=models.CASCADE,
        verbose_name=_("Education Verification"),
    )

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.education_verification.education.user.email} - {self.education_verification.education.degree} Verification"


class IEEMethod(EducationVerificationMethodAbstract):
    class EvaluatorChoices(models.TextChoices):
        WES = "wes", _("World Education Services")
        IQAS = "iqas", _("International Qualifications Assessment Service")
        ICAS = "icas", _("International Credential Assessment Service of Canada")
        CES = "ces", _("Comparative Education Service")

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
        choices=EvaluatorChoices.choices,
        verbose_name=_("Academic Credential Evaluator"),
    )

    class Meta:
        verbose_name = _("International Education Evaluation Method")
        verbose_name_plural = _("International Education Evaluation Methods")


class CommunicationMethod(EducationVerificationMethodAbstract):
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
