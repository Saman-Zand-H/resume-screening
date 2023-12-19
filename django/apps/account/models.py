import contextlib

from cities_light.models import City, Country
from colorfield.fields import ColorField
from common.models import (
    Field,
    Job,
    Language,
    LanguageProficiencyTest,
    Position,
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
from django.core import checks
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from .validators import LinkedInUsernameValidator, NameValidator, WhatsAppValidator


def full_body_image_path(instance, filename):
    return f"profile/{instance.user.id}/full_body_image/{filename}"


def get_education_verification_path(path, instance, filename):
    return f"profile/{instance.education.user.id}/education_verification/{path}/{filename}"


def get_work_experience_verification_path(path, instance, filename):
    return f"profile/{instance.work_experience.user.id}/work_experience_verification/{path}/{filename}"


def get_language_certificate_verification_path(path, instance, filename):
    return f"profile/{instance.language_certificate.user.id}/language_certificate_verification/{path}/{filename}"


def get_certificate_and_license_verification_path(path, instance, filename):
    return f"profile/{instance.certificate_and_license.user.id}/certificate_and_license_verification/{path}/{filename}"


def ices_document_path(instance, filename):
    return get_education_verification_path("ices", instance, filename)


def citizen_document_path(instance, filename):
    return get_education_verification_path("citizen", instance, filename)


def degree_file_path(instance, filename):
    return get_education_verification_path("degree", instance, filename)


def employer_letter_path(instance, filename):
    return get_work_experience_verification_path("employer_letter", instance, filename)


def paystubs_path(instance, filename):
    return get_work_experience_verification_path("paystubs", instance, filename)


def language_certificate_path(instance, filename):
    return get_language_certificate_verification_path("language_certificate", instance, filename)


def certificate_and_license_path(instance, filename):
    return get_certificate_and_license_verification_path("certificate_and_license", instance, filename)


def citizenship_document_path(instance, filename):
    return f"profile/{instance.user.id}/citizenship_document/{filename}"


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
    skills = models.ManyToManyField(Skill, verbose_name=_("Skills"), related_name="users")

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


class DocumentAbstract(models.Model):
    class Status(models.TextChoices):
        DRAFTED = "drafted", _("Drafted")
        SUBMITTED = "submitted", _("Submitted")
        REJECTED = "rejected", _("Rejected")
        VERIFIED = "verified", _("Verified")
        SELF_VERIFIED = "self_verified", _("Self Verified")

    user = models.ForeignKey(User, on_delete=models.RESTRICT, verbose_name=_("User"), related_name="%(class)ss")
    status = models.CharField(
        max_length=50,
        choices=Status.choices,
        verbose_name=_("Status"),
        default=Status.DRAFTED.value,
    )
    verified_at = models.DateTimeField(verbose_name=_("Verified At"), null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))
    allow_self_verification = models.BooleanField(default=False, verbose_name=_("Allow Self Verification"))

    class Meta:
        abstract = True

    @classmethod
    def check(cls, **kwargs):
        errors = super().check(**kwargs)
        if not cls.get_verification_abstract_model():
            errors.append(checks.Error("get_verification_abstract_model must be return a  abstract model", obj=cls))
        return errors

    @classmethod
    def get_verification_abstract_model(cls):
        return None

    @classmethod
    def get_method_models(cls):
        return get_all_subclasses(cls.get_verification_abstract_model())

    def get_verification_methods(self):
        for model in self.get_method_models():
            with contextlib.suppress(model.DoesNotExist):
                yield getattr(self, model.get_related_name())

    def get_verification_method(self):
        return next(self.get_verification_methods(), None)


class DocumentVerificationMethodAbstract(models.Model):
    verified_at = models.DateTimeField(verbose_name=_("Verified At"), null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))

    DOCUMENT_FIELD = None

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.document.user.email} - {self.document.status} Verification"

    @classmethod
    def check(cls, **kwargs):
        errors = super().check(**kwargs)
        if hasattr(cls, "DOCUMENT_FIELD") and not cls.DOCUMENT_FIELD:
            errors.append(checks.Error("DOCUMENT_FIELD must be set or is not exist", obj=cls))
        return errors

    @classmethod
    def get_document_field(cls):
        return getattr(cls, cls.DOCUMENT_FIELD).field

    @classmethod
    def get_related_name(cls):
        return cls.get_document_field().related_query_name()

    def get_document(self):
        return getattr(self, self.DOCUMENT_FIELD)

    def clean(self, *args, **kwargs):
        document = self.get_document()
        if (methods := list(document.get_verification_methods())) and len(methods) > 1:
            raise ValidationError(f"{document._meta.verbose_name} already has a verification method")


class Education(DocumentAbstract):
    class Degree(models.TextChoices):
        BACHELORS = "bachelors", _("Bachelors")
        MASTERS = "masters", _("Masters")
        PHD = "phd", _("PhD")
        ASSOCIATE = "associate", _("Associate")
        DIPLOMA = "diploma", _("Diploma")
        CERTIFICATE = "certificate", _("Certificate")

    field = models.ForeignKey(Field, on_delete=models.CASCADE, verbose_name=_("Field"))
    degree = models.CharField(max_length=50, choices=Degree.choices, verbose_name=_("Degree"))
    university = models.ForeignKey(University, on_delete=models.CASCADE, verbose_name=_("University"))
    start = models.DateField(verbose_name=_("Start Date"))
    end = models.DateField(verbose_name=_("End Date"), null=True, blank=True)

    class Meta:
        verbose_name = _("Education")
        verbose_name_plural = _("Educations")

    @classmethod
    def get_verification_abstract_model(cls):
        return EducationVerificationMethodAbstract

    def clean(self):
        if self.end and self.start > self.end:
            raise ValidationError({"end": _("End date must be after Start date")})
        return super().clean()


class EducationVerificationMethodAbstract(DocumentVerificationMethodAbstract):
    education = models.OneToOneField(
        Education,
        on_delete=models.CASCADE,
        verbose_name=_("Education"),
    )
    DOCUMENT_FIELD = "education"

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.education.user.email} - {self.education.degree} Verification"


class IEEMethod(EducationVerificationMethodAbstract):
    class Evaluator(models.TextChoices):
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
        choices=Evaluator.choices,
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


class WorkExperience(DocumentAbstract):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, verbose_name=_("Job"), related_name="work_experiences")
    start = models.DateField(verbose_name=_("Start Date"))
    end = models.DateField(verbose_name=_("End Date"), null=True, blank=True)
    skills = models.ManyToManyField(Skill, verbose_name=_("Skills"), related_name="work_experiences")
    organization = models.CharField(max_length=255, verbose_name=_("Organization"))
    city = models.ForeignKey(City, on_delete=models.CASCADE, verbose_name=_("City"), related_name="work_experiences")

    class Meta:
        verbose_name = _("Work Experience")
        verbose_name_plural = _("Work Experiences")

    def __str__(self):
        return f"{self.user.email} - {self.job.title} - {self.organization}"

    @classmethod
    def get_verification_abstract_model(cls):
        return WorkExperienceVerificationMethodAbstract

    def clean(self):
        if self.end and self.start > self.end:
            raise ValidationError({"end": _("End date must be after Start date")})
        return super().clean()


class WorkExperienceVerificationMethodAbstract(DocumentVerificationMethodAbstract):
    work_experience = models.OneToOneField(WorkExperience, on_delete=models.CASCADE, verbose_name=_("Work Experience"))
    DOCUMENT_FIELD = "work_experience"

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.work_experience} Verification"


class EmployerLetterMethod(WorkExperienceVerificationMethodAbstract):
    employer_letter = models.FileField(
        upload_to=employer_letter_path,
        verbose_name=_("Employer Letter"),
        validators=[DOCUMENT_FILE_EXTENSION_VALIDATOR, DOCUMENT_FILE_SIZE_VALIDATOR],
    )

    class Meta:
        verbose_name = _("Employer Letter Method")
        verbose_name_plural = _("Employer Letter Methods")


class PaystubsMethod(WorkExperienceVerificationMethodAbstract):
    paystubs = models.FileField(
        upload_to=paystubs_path,
        verbose_name=_("Employer Letter"),
        validators=[DOCUMENT_FILE_EXTENSION_VALIDATOR, DOCUMENT_FILE_SIZE_VALIDATOR],
    )

    class Meta:
        verbose_name = _("Paystubs Method")
        verbose_name_plural = _("Paystubs Methods")


class ReferenceCheckEmployer(models.Model):
    work_experience_verification = models.ForeignKey(
        EmployerLetterMethod,
        on_delete=models.CASCADE,
        verbose_name=_("Work Experience Verification"),
        related_name="employers",
    )
    name = models.CharField(max_length=255, verbose_name=_("Name"))
    email = models.EmailField(verbose_name=_("Email"))
    phone_number = PhoneNumberField(verbose_name=_("Phone Number"))
    position = models.ForeignKey(Position, on_delete=models.CASCADE, verbose_name=_("Position"))

    class Meta:
        verbose_name = _("Reference Check Employer")
        verbose_name_plural = _("Reference Check Employers")

    def __str__(self):
        return f"{self.work_experience_verification} - {self.name}"


class LanguageCertificate(DocumentAbstract):
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

    @classmethod
    def get_verification_abstract_model(cls):
        return LanguageCertificateVerificationMethodAbstract

    def clean(self):
        if not all(
            self.test.min_score <= score <= self.test.max_score
            for score in (
                self.listening_score,
                self.reading_score,
                self.writing_score,
                self.speaking_score,
            )
        ):
            raise ValidationError(_("All scores must be between minimum and maximum score of the test"))

        if not self.test.overall_min_score <= self.band_score <= self.test.overall_max_score:
            raise ValidationError(
                {"band_score": _("Band score must be between overall minimum and maximum score of the test")}
            )

        if self.issued_at > self.expired_at:
            raise ValidationError({"expired_at":_("Expired date must be after Issued date")})
        return super().clean()


class LanguageCertificateVerificationMethodAbstract(DocumentVerificationMethodAbstract):
    language_certificate = models.OneToOneField(
        LanguageCertificate, on_delete=models.CASCADE, verbose_name=_("Language Certificate")
    )
    DOCUMENT_FIELD = "language_certificate"

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.language_certificate.test.title} ({self.language_certificate.language.name}) Verification"


class OfflineMethod(LanguageCertificateVerificationMethodAbstract):
    certificate_file = models.FileField(
        upload_to=language_certificate_path,
        verbose_name=_("Language Certificate"),
        validators=[DOCUMENT_FILE_EXTENSION_VALIDATOR, DOCUMENT_FILE_SIZE_VALIDATOR],
    )

    class Meta:
        verbose_name = _("Offline Method")
        verbose_name_plural = _("Offline Methods")


class OnlineMethod(LanguageCertificateVerificationMethodAbstract):
    certificate_link = models.URLField(verbose_name=_("Link"))

    class Meta:
        verbose_name = _("Online Method")
        verbose_name_plural = _("Online Methods")


class CertificateAndLicense(DocumentAbstract):
    title = models.CharField(max_length=255, verbose_name=_("Title"))
    certifier = models.CharField(max_length=255, verbose_name=_("Certifier"))
    issued_at = models.DateField(verbose_name=_("Issued At"))
    expired_at = models.DateField(verbose_name=_("Expired At"), null=True, blank=True)

    class Meta:
        verbose_name = _("Certificate And License")
        verbose_name_plural = _("Certificates And Licenses")

    def __str__(self):
        return f"{self.user.email} - {self.title}"

    @classmethod
    def get_verification_abstract_model(cls):
        return CertificateAndLicenseVerificationMethodAbstract

    def clean(self):
        if self.expired_at and self.issued_at > self.expired_at:
            raise ValidationError({"expired_at":_("Expired date must be after Issued date")})
        return super().clean()


class CertificateAndLicenseVerificationMethodAbstract(DocumentVerificationMethodAbstract):
    certificate_and_license = models.OneToOneField(
        CertificateAndLicense, on_delete=models.CASCADE, verbose_name=_("Certificate And License")
    )
    DOCUMENT_FIELD = "certificate_and_license"

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.certificate_and_license.title} Verification"


class CertificateAndLicenseOfflineVerificationMethod(CertificateAndLicenseVerificationMethodAbstract):
    certificate_file = models.FileField(
        upload_to=certificate_and_license_path,
        verbose_name=_("Certificate And License"),
        validators=[DOCUMENT_FILE_EXTENSION_VALIDATOR, DOCUMENT_FILE_SIZE_VALIDATOR],
    )

    class Meta:
        verbose_name = _("Certificate And License Offline Verification Method")
        verbose_name_plural = _("Certificate And License Offline Verification Methods")


class CertificateAndLicenseOnlineVerificationMethod(CertificateAndLicenseVerificationMethodAbstract):
    certificate_link = models.URLField(verbose_name=_("Link"))

    class Meta:
        verbose_name = _("Certificate And License Online Verification Method")
        verbose_name_plural = _("Certificate And License Online Verification Methods")


class CanadaVisa(models.Model):
    class Status(models.TextChoices):
        STUDY_PERMIT = "study_permit", _("Study Permit")
        WORK_PERMIT = "work_permit", _("Work Permit")
        PERMANENT_RESIDENCY = "permanent_residency", _("Permanent Residency")
        VISITOR_VISA = "visitor_visa", _("Visitor Visa")
        REFUGEE_STATUS = "refugee_status", _("Refugee Status")
        CITIZENSHIP = "citizenship", _("Citizenship")
        TEMPORARY_RESIDENCY = "temporary_residency", _("Temporary Residency")
        PENDING = "pending", _("Pending")
        OTHER = "other", _("Other")

    user = models.OneToOneField(User, on_delete=models.RESTRICT, verbose_name=_("User"), related_name="canada_visa")
    nationality = models.ForeignKey(
        Country, on_delete=models.CASCADE, verbose_name=_("Nationality"), related_name="canada_visas"
    )
    status = models.CharField(
        max_length=50,
        choices=Status.choices,
        verbose_name=_("Status"),
    )
    citizenship_document = models.FileField(
        upload_to=citizenship_document_path,
        verbose_name=_("Citizenship Document"),
        validators=[DOCUMENT_FILE_EXTENSION_VALIDATOR, DOCUMENT_FILE_SIZE_VALIDATOR],
    )
