import contextlib

from cities_light.models import City
from colorfield.fields import ColorField
from common.models import (
    Field,
    Job,
    Language,
    LanguageProficiencyTest,
    Skill,
    University,
)
from common.utils import get_all_subclasses
from common.validators import (
    DOCUMENT_FILE_EXTENSION_VALIDATOR,
    DOCUMENT_FILE_SIZE_VALIDATOR,
    IMAGE_FILE_SIZE_VALIDATOR,
)
from phonenumber_field.modelfields import PhoneNumberField
from phonenumber_field.phonenumber import PhoneNumber
from phonenumbers.phonenumberutil import NumberParseException

from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import UserManager as BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _

from .validators import LinkedInUsernameValidator, NameValidator, WhatsAppValidator


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


def fix_whatsapp_value(value):
    with contextlib.suppress(NumberParseException):
        return PhoneNumber.from_string(value).as_e164
    return value


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

    FIELDS_PROPERTIES = {
        "email": {
            "_unique": True,
            "blank": False,
            "null": False,
        },
        "username": {
            "blank": True,
            "null": True,
        },
        "first_name": {
            "validators": [NameValidator()],
        },
        "last_name": {
            "validators": [NameValidator()],
        },
    }

    gender = models.CharField(
        max_length=50,
        choices=Gender.choices,
        verbose_name=_("Gender"),
        null=True,
        blank=True,
    )
    birth_date = models.DateField(verbose_name=_("Birth Date"), null=True, blank=True)

    objects = UserManager()


for field, properties in User.FIELDS_PROPERTIES.items():
    for key, value in properties.items():
        setattr(User._meta.get_field(field), key, value)


class Profile(models.Model):
    class SkinColor(models.TextChoices):
        VERY_FAIR = "#FFDFC4", _("Very Fair")
        FAIR = "#F0D5B1", _("Fair")
        LIGHT = "#E5B897", _("Light")
        LIGHT_MEDIUM = "#D9A377", _("Light Medium")
        MEDIUM = "#C68642", _("Medium")
        OLIVE = "#A86B33", _("Olive")
        BROWN = "#8D5524", _("Brown")
        DARK_BROWN = "#60391C", _("Dark Brown")
        VERY_DARK = "#3B260B", _("Very Dark")
        DEEP = "#100C08", _("Deep")

    class EyeColor(models.TextChoices):
        AMBER = "#FFBF00", _("Amber")
        BLUE = "#5DADEC", _("Blue")
        BROWN = "#6B4226", _("Brown")
        GRAY = "#BEBEBE", _("Gray")
        GREEN = "#1CAC78", _("Green")
        HAZEL = "#8E7618", _("Hazel")

    class EmploymentStatus(models.TextChoices):
        EMPLOYED = "employed", _("Employed")
        UNEMPLOYED = "unemployed", _("Unemployed")

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
    employment_status = models.CharField(
        max_length=50,
        choices=EmploymentStatus.choices,
        verbose_name=_("Employment Status"),
        null=True,
        blank=True,
    )
    interested_jobs = models.ManyToManyField(Job, verbose_name=_("Interested Jobs"), blank=True)
    city = models.ForeignKey(City, on_delete=models.SET_NULL, verbose_name=_("City"), null=True, blank=True)

    class Meta:
        verbose_name = _("User Profile")
        verbose_name_plural = _("User Profiles")

    def __str__(self):
        return self.user.email


class Contact(models.Model):
    class Type(models.TextChoices):
        WEBSITE = "website", _("Website")
        ADDRESS = "address", _("Address")
        LINKEDIN = "linkedin", _("LinkedIn")
        WHATSAPP = "whatsapp", _("WhatsApp")
        PHONE = "phone", _("Phone")

    VALIDATORS = {
        Type.WEBSITE: models.URLField().run_validators,
        Type.ADDRESS: None,
        Type.LINKEDIN: LinkedInUsernameValidator(),
        Type.WHATSAPP: WhatsAppValidator(),
        Type.PHONE: PhoneNumberField().run_validators,
    }

    VALUE_FIXERS = {
        Type.PHONE: lambda value: PhoneNumber.from_string(value).as_e164,
        Type.WHATSAPP: fix_whatsapp_value,
    }

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_("User"), related_name="contacts")
    type = models.CharField(
        max_length=50,
        choices=Type.choices,
        verbose_name=_("Type"),
        default=Type.WEBSITE.value,
    )
    value = models.CharField(max_length=255, verbose_name=_("Value"))

    class Meta:
        unique_together = ("user", "type")
        verbose_name = _("Contact")
        verbose_name_plural = _("Contacts")

    def __str__(self):
        return f"{self.user.email} - {self.type}: {self.value}"

    def clean(self, *args, **kwargs):
        if self.type in self.VALIDATORS:
            with contextlib.suppress(TypeError):
                self.VALIDATORS[self.type](self.value)
        else:
            raise NotImplementedError(f"Validation for {self.type} is not implemented")

        if self.type in self.VALUE_FIXERS:
            self.value = self.VALUE_FIXERS[self.type](self.value)


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
        return get_all_subclasses(EducationVerificationMethodAbstract)

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


class WorkExperience(models.Model):
    class Status(models.TextChoices):
        SUBMITED = "submited", _("Submited")
        DRAFT = "draft", _("Draft")

    user = models.ForeignKey(User, on_delete=models.RESTRICT, verbose_name=_("User"), related_name="work_experiences")
    job = models.ForeignKey(Job, on_delete=models.CASCADE, verbose_name=_("Job"), related_name="work_experiences")
    start = models.DateField(verbose_name=_("Start Date"))
    end = models.DateField(verbose_name=_("End Date"), null=True, blank=True)
    skills = models.ManyToManyField(Skill, verbose_name=_("Skills"), related_name="work_experiences")
    # TODO: check if organization field is a foreignkey
    organization = models.CharField(max_length=255, verbose_name=_("Organization"))
    city = models.ForeignKey(City, on_delete=models.CASCADE, verbose_name=_("City"), related_name="work_experiences")
    status = models.CharField(max_length=50, choices=Status.choices, verbose_name=_("Status"))

    class Meta:
        verbose_name = _("Work Experience")
        verbose_name_plural = _("Work Experiences")

    def __str__(self):
        return f"{self.user.email} - {self.job.title} - {self.organization}"


class LanguageCertificate(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.RESTRICT, verbose_name=_("User"), related_name="language_certificates"
    )
    language = models.ForeignKey(
        Language, on_delete=models.CASCADE, verbose_name=_("Language"), related_name="certificates"
    )
    test = models.ForeignKey(
        LanguageProficiencyTest, on_delete=models.CASCADE, verbose_name=_("Test"), related_name="certificates"
    )
    issued_at = models.DateField(verbose_name=_("Issued At"))
    expired_at = models.DateField(verbose_name=_("Expired At"))
    listening_score = models.FloatField(verbose_name=_("Listening Score"))
    reading_score = models.FloatField(verbose_name=_("Reading Score"))
    writing_score = models.FloatField(verbose_name=_("Writing Score"))
    speaking_score = models.FloatField(verbose_name=_("Speaking Score"))
    band_score = models.FloatField(verbose_name=_("Band Score"))

    class Meta:
        verbose_name = _("Language Certificate")
        verbose_name_plural = _("Language Certificates")

    def __str__(self):
        return f"{self.user.email} - {self.language.name} - {self.test.title}"


class CertificateAndLicense(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.RESTRICT, verbose_name=_("User"), related_name="certificate_and_licenses"
    )
    title = models.CharField(max_length=255, verbose_name=_("Title"))
    certifier = models.CharField(max_length=255, verbose_name=_("Certifier"))
    issued_at = models.DateField(verbose_name=_("Issued At"))
    expired_at = models.DateField(verbose_name=_("Expired At"), null=True, blank=True)

    class Meta:
        verbose_name = _("Certificate And License")
        verbose_name_plural = _("Certificates And Licenses")


class UserSkill(models.Model):
    user = models.ForeignKey(User, on_delete=models.RESTRICT, verbose_name=_("User"), related_name="skills")
    skills = models.ManyToManyField(Skill, verbose_name=_("Skills"), related_name="users")

    class Meta:
        verbose_name = _("User Skill")
        verbose_name_plural = _("User Skills")
