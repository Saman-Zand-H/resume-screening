import base64
import contextlib
import uuid
from typing import Optional

from cities_light.models import City, Country
from colorfield.fields import ColorField
from common.choices import LANGUAGES
from common.mixins import HasDurationMixin
from common.models import (
    Field,
    FileModel,
    Job,
    LanguageProficiencySkill,
    LanguageProficiencyTest,
    Skill,
    University,
)
from common.utils import get_all_subclasses
from common.validators import (
    DOCUMENT_FILE_EXTENSION_VALIDATOR,
    DOCUMENT_FILE_SIZE_VALIDATOR,
    IMAGE_FILE_EXTENSION_VALIDATOR,
    IMAGE_FILE_SIZE_VALIDATOR,
)
from computedfields.models import ComputedFieldsModel, computed
from flex_eav.models import EavValue
from flex_pubsub.tasks import task_registry
from phonenumber_field.modelfields import PhoneNumberField
from phonenumber_field.phonenumber import PhoneNumber
from phonenumbers.phonenumberutil import NumberParseException

from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.fields import ArrayField
from django.core import checks
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import models, transaction
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from .managers import CertificateAndLicenseManager, UserManager
from .validators import LinkedInUsernameValidator, NameValidator, WhatsAppValidator


def avatar_path(instance, filename):
    return f"profile/{instance.user.id}/avatar/{filename}"


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


def education_evaluation_document_path(instance, filename):
    return get_education_verification_path("education_evaluation", instance, filename)


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


def resume_path(instance, filename):
    return f"profile/{instance.user.id}/resume/{filename}"


def fix_whatsapp_value(value):
    with contextlib.suppress(NumberParseException):
        return PhoneNumber.from_string(value).as_e164
    return value


def generate_unique_referral_code():
    return base64.b32encode(uuid.uuid4().bytes).decode("utf-8")[:8]


def generate_ticket_id():
    return str(uuid.uuid4())[:8]


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
            "db_index": True,
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
    raw_skills = ArrayField(models.CharField(max_length=64), verbose_name=_("Raw Skills"), blank=True, null=True)
    skills = models.ManyToManyField(Skill, verbose_name=_("Skills"), related_name="users", editable=False)
    available_jobs = models.ManyToManyField(Job, verbose_name=_("Available Jobs"), blank=True)

    objects = UserManager()

    @property
    def has_resume(self):
        for field in self.get_resume_related_models():
            field_name = field.field.related_query_name()
            with contextlib.suppress(field.field.model.DoesNotExist):
                value = getattr(self, field_name)
                if value is not None and (isinstance(value, models.Model) or value.exists()):
                    return True
        return False

    def get_resume_related_models(self):
        return (
            Resume.user,
            Profile.user,
            Education.user,
            WorkExperience.user,
            LanguageCertificate.user,
            CertificateAndLicense.user,
        )


for field, properties in User.FIELDS_PROPERTIES.items():
    for key, value in properties.items():
        setattr(User._meta.get_field(field), key, value)


class UserFile(FileModel):
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="%(class)s")

    class Meta:
        abstract = True

    def check_auth(self, request):
        return request.user == self.uploaded_by

    @classmethod
    def get_user_temporary_file(cls, user: User) -> Optional["UserFile"]:
        return cls.objects.filter(
            uploaded_by=user, **{field.field.related_query_name(): None for field in cls.get_related_fields()}
        ).first()

    @classmethod
    def is_used(cls, user: User) -> bool:
        return (
            cls.objects.filter(uploaded_by=user)
            .exclude(**{field.field.related_query_name(): None for field in cls.get_related_fields()})
            .exists()
        )

    @classmethod
    @transaction.atomic
    def create_temporary_file(cls, file: InMemoryUploadedFile, user: User):
        obj = cls.objects.filter(uploaded_by=user).first()
        if obj:
            obj.update_temporary_file(file)
        else:
            obj = cls(uploaded_by=user, file=file)
            obj.full_clean()
            obj.save()
        return obj

    def update_temporary_file(self, file: InMemoryUploadedFile):
        self.file = file
        self.full_clean()
        self.save()
        return self


class UserUploadedDocumentFile(UserFile):
    class Meta:
        abstract = True

    def get_validators(self):
        return [DOCUMENT_FILE_EXTENSION_VALIDATOR, DOCUMENT_FILE_SIZE_VALIDATOR]


class UserUploadedImageFile(UserFile):
    class Meta:
        abstract = True

    def get_validators(self):
        return [IMAGE_FILE_EXTENSION_VALIDATOR, IMAGE_FILE_SIZE_VALIDATOR]


class AvatarFile(UserUploadedImageFile):
    SLUG = "avatar"

    def get_upload_path(self, filename):
        return f"profile/{self.uploaded_by.id}/avatar/{filename}"

    class Meta:
        verbose_name = _("Avatar Image")
        verbose_name_plural = _("Avatar Images")


class FullBodyImageFile(UserUploadedImageFile):
    SLUG = "full_body_image"

    def get_upload_path(self, filename):
        return f"profile/{self.uploaded_by.id}/full_body_image/{filename}"

    class Meta:
        verbose_name = _("Full Body Image")
        verbose_name_plural = _("Full Body Images")


class Profile(ComputedFieldsModel):
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

    class JobType(models.TextChoices):
        FULL_TIME = "full_time", _("Full Time")
        PART_TIME = "part_time", _("Part Time")
        PERMANENT = "permanent", _("Permanent")
        FIX_TERM_CONTRACT = "fix_term_contract", _("Fix Term Contract")
        SEASONAL = "seasonal", _("Seasonal")
        FREELANCE = "freelance", _("Freelance")
        APPRENTICESHIP = "apprenticeship", _("Apprenticeship")
        PRINCE_EDWARD_ISLAND = "prince_edward_island", _("Prince Edward Island")
        INTERNSHIP_CO_OP = "internship_co_op", _("Internship/Co-op")

    class JobLocationType(models.TextChoices):
        PRECISE_LOCATION = "precise_location", _("On-site (Precise Location)")
        LIMITED_AREA = "limited_area", _("On-site (Within a Limited Area)")
        REMOTE = "remote", _("Remote")
        HYBRID = "hybrid", _("Hybrid")
        ON_THE_ROAD = "on_the_road", _("On the road")
        GLOBAL = "global", _("Global")

    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name=_("User"))
    height = models.IntegerField(null=True, blank=True)
    weight = models.IntegerField(null=True, blank=True)
    skin_color = ColorField(choices=SkinColor.choices, null=True, blank=True, verbose_name=_("Skin Color"))
    hair_color = ColorField(null=True, blank=True, verbose_name=_("Hair Color"))
    eye_color = ColorField(choices=EyeColor.choices, null=True, blank=True, verbose_name=_("Eye Color"))
    avatar_x = models.OneToOneField(
        AvatarFile,
        on_delete=models.SET_NULL,
        related_name="profile_x",
        null=True,
        blank=True,
        verbose_name=_("Avatar"),
    )
    avatar = models.ForeignKey(
        AvatarFile,
        on_delete=models.CASCADE,
        related_name="profile",
        null=True,
        blank=True,
    )
    full_body_image_x = models.OneToOneField(
        FullBodyImageFile,
        on_delete=models.SET_NULL,
        related_name="profile_x",
        null=True,
        blank=True,
        verbose_name=_("Full Body Image"),
    )
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
    city = models.ForeignKey(
        City,
        on_delete=models.SET_NULL,
        verbose_name=_("City"),
        null=True,
        blank=True,
        related_name="profiles",
    )
    native_language = models.CharField(
        choices=LANGUAGES,
        max_length=32,
        verbose_name=_("Native Language"),
        null=True,
        blank=True,
    )
    fluent_languages = ArrayField(
        models.CharField(choices=LANGUAGES, max_length=32),
        verbose_name=_("Fluent Languages"),
        null=True,
        blank=True,
    )
    job_cities = models.ManyToManyField(City, verbose_name=_("Job City"), related_name="job_profiles", blank=True)
    job_type = ArrayField(
        models.CharField(max_length=50, choices=JobType.choices),
        verbose_name=_("Job Type"),
        null=True,
        blank=True,
    )
    job_location_type = ArrayField(
        models.CharField(max_length=50, choices=JobLocationType.choices),
        verbose_name=_("Job Location Type"),
        null=True,
        blank=True,
    )

    @computed(
        models.JSONField(verbose_name=_("Scores"), default=dict),
        depends=[
            ("self", ["city", "fluent_languages", "native_language"]),
            ("user", ["first_name", "last_name", "email", "gender", "birth_date"]),
            ("user.contacts", ["id"]),
            ("user.resume", ["id"]),
            ("user.educations", ["id", "status"]),
            ("user.workexperiences", ["id", "status"]),
            ("user.languagecertificates", ["id", "status"]),
            ("user.certificateandlicenses", ["id", "status"]),
            ("user.skills", ["id"]),
            ("user.canada_visa", ["id"]),
            ("interested_jobs", ["id"]),
            ("user.job_assessment_results", ["status"]),
            ("user.referral", ["id"]),
            ("user.referral.referred_users", ["id"]),
        ],
    )
    def scores(self):
        from .scores import UserScorePack

        scores = UserScorePack.calculate(self.user)

        return {
            "total": sum(scores.values()),
            "scores": scores,
        }

    @computed(
        models.IntegerField(verbose_name=_("Credits")),
        depends=[
            ("user.referral.referred_users", ["id"]),
        ],
        prefetch_related=["user__referral__referred_users"],
    )
    def credits(self):
        _credits = 0
        with contextlib.suppress(ObjectDoesNotExist):
            _credits += self.user.referral.referred_users.count() * 100
        return _credits

    @property
    def score(self):
        return self.scores.get("total", 0)

    @property
    def completion_percentage(self):
        related_scores = self.get_completion_related_scores()
        scores = self.scores.get("scores", {})
        completed_scores = sum(1 for score in related_scores if scores.get(score.slug, 0))
        return (completed_scores / len(related_scores)) * 100

    class Meta:
        verbose_name = _("User Profile")
        verbose_name_plural = _("User Profiles")

    def __str__(self):
        return self.user.email

    @staticmethod
    def get_appearance_related_fields():
        return (
            Profile.height.field.name,
            Profile.weight.field.name,
            Profile.skin_color.field.name,
            Profile.hair_color.field.name,
            Profile.eye_color.field.name,
            Profile.full_body_image.field.name,
        )

    @staticmethod
    def get_completion_related_scores():
        from . import scores

        return [
            scores.FirstNameScore,
            scores.LastNameScore,
            scores.GenderScore,
            scores.DateOfBirthScore,
            scores.EmailScore,
            scores.CityScore,
            scores.MobileScore,
            scores.EducationNewScore,
            scores.EducationVerificationScore,
            scores.WorkExperienceNewScore,
            scores.WorkExperienceVerificationScore,
            scores.LanguageScore,
            scores.FluentLanguageScore,
            scores.NativeLanguageScore,
            scores.CertificationScore,
            scores.SkillScore,
            scores.VisaStatusScore,
            scores.JobInterestScore,
        ]

    @property
    def has_appearance_related_data(self):
        return all(getattr(self, field) is not None for field in Profile.get_appearance_related_fields())


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
                try:
                    self.VALIDATORS[self.type](self.value)
                except ValidationError as e:
                    raise ValidationError({self.type: next(iter(e.messages))}) from e
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

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_("User"), related_name="%(class)ss")
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

    @classmethod
    def get_verified_statuses(cls):
        return (cls.Status.VERIFIED,)


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


class Education(DocumentAbstract, HasDurationMixin):
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
    city = models.ForeignKey(City, on_delete=models.CASCADE, verbose_name=_("City"))
    start = models.DateField(verbose_name=_("Start Date"))
    end = models.DateField(verbose_name=_("End Date"), null=True, blank=True)

    class Meta:
        verbose_name = _("Education")
        verbose_name_plural = _("Educations")

    @cached_property
    def title(self):
        return f"{self.get_degree_display()} in {self.field.name}"

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


class EducationEvaluationDocumentFile(UserUploadedDocumentFile):
    SLUG = "education_evaluation"

    def get_upload_path(self, filename):
        return f"profile/{self.uploaded_by.id}/education_verification/education_evaluation/{filename}"

    class Meta:
        verbose_name = _("Education Evaluation Document File")
        verbose_name_plural = _("Education Evaluation Document Files")


class IEEMethod(EducationVerificationMethodAbstract):
    class Evaluator(models.TextChoices):
        WES = "wes", _("World Education Services")
        IQAS = "iqas", _("International Qualifications Assessment Service")
        ICAS = "icas", _("International Credential Assessment Service of Canada")
        CES = "ces", _("Comparative Education Service")
        OTHER = "other", _("Other")

    education_evaluation_document_x = models.OneToOneField(
        EducationEvaluationDocumentFile,
        on_delete=models.CASCADE,
        related_name="iee_method_x",
        verbose_name=_("Education Evaluation Document"),
        null=True,  # TODO: remove this
        default=None,  # TODO: remove this
    )
    education_evaluation_document = models.FileField(
        upload_to=education_evaluation_document_path,
        verbose_name=_("Education Evaluation Document"),
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


class DegreeFile(UserUploadedDocumentFile):
    SLUG = "degree"

    def get_upload_path(self, filename):
        return f"profile/{self.uploaded_by.id}/education_verification/degree/{filename}"

    class Meta:
        verbose_name = _("Degree File")
        verbose_name_plural = _("Degree Files")


class CommunicationMethod(EducationVerificationMethodAbstract):
    website = models.URLField(verbose_name=_("Website"))
    email = models.EmailField(verbose_name=_("Email"))
    department = models.CharField(max_length=255, verbose_name=_("Department"))
    person = models.CharField(max_length=255, verbose_name=_("Person"))
    degree_file_x = models.OneToOneField(
        DegreeFile,
        on_delete=models.CASCADE,
        related_name="communication_method_x",
        verbose_name=_("Degree File"),
        null=True,  # TODO: remove this
        default=None,  # TODO: remove this
    )
    degree_file = models.FileField(
        upload_to=degree_file_path,
        verbose_name=_("Degree File"),
        validators=[DOCUMENT_FILE_EXTENSION_VALIDATOR, DOCUMENT_FILE_SIZE_VALIDATOR],
    )

    class Meta:
        verbose_name = _("Communication Method")
        verbose_name_plural = _("Communication Methods")


class WorkExperience(DocumentAbstract, HasDurationMixin):
    class Grade(models.TextChoices):
        INTERN = "intern", _("Intern")
        ASSOCIATE = "associate", _("Associate")
        JUNIOR = "junior", _("Junior")
        MID_LEVEL = "mid_level", _("Mid-Level")
        SENIOR = "senior", _("Senior")
        MANAGER = "manager", _("Manager")
        DIRECTOR = "director", _("Director")
        CTO = "cto", _("CTO")
        CFO = "cfo", _("CFO")
        CEO = "ceo", _("CEO")

    job = models.ForeignKey(Job, on_delete=models.CASCADE, verbose_name=_("Job"), related_name="work_experiences")
    grade = models.CharField(max_length=50, choices=Grade.choices, verbose_name=_("Grade"))
    start = models.DateField(verbose_name=_("Start Date"))
    end = models.DateField(verbose_name=_("End Date"), null=True, blank=True)
    organization = models.CharField(max_length=255, verbose_name=_("Organization"))
    city = models.ForeignKey(City, on_delete=models.CASCADE, verbose_name=_("City"), related_name="work_experiences")
    skills = models.CharField(max_length=250, verbose_name=_("Skills"), blank=True, null=True)

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


class EmployerLetterFile(UserUploadedDocumentFile):
    SLUG = "employer_letter"

    def get_upload_path(self, filename):
        return f"profile/{self.uploaded_by.id}/work_experience_verification/employer_letter/{filename}"

    class Meta:
        verbose_name = _("Employer Letter File")
        verbose_name_plural = _("Employer Letter Files")


class EmployerLetterMethod(WorkExperienceVerificationMethodAbstract):
    employer_letter_x = models.OneToOneField(
        EmployerLetterFile,
        on_delete=models.CASCADE,
        related_name="employer_letter_method_x",
        verbose_name=_("Employer Letter"),
        null=True,  # TODO: remove this
        default=None,  # TODO: remove this
    )

    employer_letter = models.FileField(
        upload_to=employer_letter_path,
        verbose_name=_("Employer Letter"),
        validators=[DOCUMENT_FILE_EXTENSION_VALIDATOR, DOCUMENT_FILE_SIZE_VALIDATOR],
    )

    class Meta:
        verbose_name = _("Employer Letter Method")
        verbose_name_plural = _("Employer Letter Methods")


class PaystubsFile(UserUploadedDocumentFile):
    SLUG = "paystubs"

    def get_upload_path(self, filename):
        return f"profile/{self.uploaded_by.id}/work_experience_verification/paystubs/{filename}"

    class Meta:
        verbose_name = _("Paystubs File")
        verbose_name_plural = _("Paystubs Files")


class PaystubsMethod(WorkExperienceVerificationMethodAbstract):
    paystubs_x = models.OneToOneField(
        PaystubsFile,
        on_delete=models.CASCADE,
        related_name="paystubs_method_x",
        verbose_name=_("Paystubs"),
        null=True,  # TODO: remove this
        default=None,  # TODO: remove this
    )

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
    position = models.CharField(max_length=255, verbose_name=_("Position"))

    class Meta:
        verbose_name = _("Reference Check Employer")
        verbose_name_plural = _("Reference Check Employers")

    def __str__(self):
        return f"{self.work_experience_verification} - {self.name}"


class LanguageCertificate(DocumentAbstract):
    language = models.CharField(choices=LANGUAGES, max_length=32, verbose_name=_("Language"))
    test = models.ForeignKey(
        LanguageProficiencyTest,
        on_delete=models.CASCADE,
        verbose_name=_("Test"),
        related_name="certificates",
    )
    issued_at = models.DateField(verbose_name=_("Issued At"))
    expired_at = models.DateField(verbose_name=_("Expired At"))

    def __str__(self):
        return f"{self.user.email} - {self.language}"

    class Meta:
        verbose_name = _("Language Certificate")
        verbose_name_plural = _("Language Certificates")

    @classmethod
    def get_verification_abstract_model(cls):
        return LanguageCertificateVerificationMethodAbstract

    def clean(self):
        if self.issued_at > self.expired_at:
            raise ValidationError({"expired_at": _("Expired date must be after Issued date")})

        if self.language not in self.test.languages:
            raise ValidationError(
                {
                    LanguageCertificate.language.field.name: _("Language must be one of the following: %s")
                    % ", ".join(self.test.languages)
                }
            )

        return super().clean()


class LanguageCertificateValue(EavValue):
    attribute_field_name = "skill"
    language_certificate = models.ForeignKey(
        LanguageCertificate,
        on_delete=models.CASCADE,
        verbose_name=_("Language Certificate"),
        related_name="values",
    )
    skill = models.ForeignKey(
        LanguageProficiencySkill,
        on_delete=models.CASCADE,
        related_name="results",
        verbose_name=_("Skill"),
    )

    class Meta:
        verbose_name = _("Language Certificate Value")
        verbose_name_plural = _("Language Certificate Values")

    def __str__(self):
        return f"{self.skill} - {self.value}"

    def clean(self):
        try:
            super().clean()
        except ValidationError as e:
            raise ValidationError({LanguageCertificateValue.value.field.name: e.error_list[0].message})


class LanguageCertificateVerificationMethodAbstract(DocumentVerificationMethodAbstract):
    language_certificate = models.OneToOneField(
        LanguageCertificate, on_delete=models.CASCADE, verbose_name=_("Language Certificate")
    )
    DOCUMENT_FIELD = "language_certificate"

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.language_certificate.test.title} ({self.language_certificate.language}) Verification"


class LanguageCertificateFile(UserUploadedDocumentFile):
    SLUG = "language_certificate"

    def get_upload_path(self, filename):
        return f"profile/{self.uploaded_by.id}/language_certificate_verification/language_certificate/{filename}"

    class Meta:
        verbose_name = _("Language Certificate File")
        verbose_name_plural = _("Language Certificate Files")


class OfflineMethod(LanguageCertificateVerificationMethodAbstract):
    certificate_file_x = models.OneToOneField(
        LanguageCertificateFile,
        on_delete=models.CASCADE,
        related_name="offline_method_x",
        verbose_name=_("Language Certificate"),
        null=True,  # TODO: remove this
        default=None,  # TODO: remove this
    )

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


class CertificateAndLicense(DocumentAbstract, HasDurationMixin):
    start_date_field = "issued_at"
    end_date_field = "expired_at"

    title = models.CharField(max_length=255, verbose_name=_("Title"))
    certifier = models.CharField(max_length=255, verbose_name=_("Certifier"))
    issued_at = models.DateField(verbose_name=_("Issued At"))
    expired_at = models.DateField(verbose_name=_("Expired At"), null=True, blank=True)

    objects = CertificateAndLicenseManager()

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
            raise ValidationError({"expired_at": _("Expired date must be after Issued date")})
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


class CertificateFile(UserUploadedDocumentFile):
    SLUG = "certificate"

    def get_upload_path(self, filename):
        return f"profile/{self.uploaded_by.id}/certificate_and_license_verification/certificate_and_license/{filename}"

    class Meta:
        verbose_name = _("Certificate File")
        verbose_name_plural = _("Certificate Files")


class CertificateAndLicenseOfflineVerificationMethod(CertificateAndLicenseVerificationMethodAbstract):
    certificate_file_x = models.OneToOneField(
        CertificateFile,
        on_delete=models.CASCADE,
        related_name="offline_method_x",
        verbose_name=_("Certificate And License"),
        null=True,  # TODO: remove this
        default=None,  # TODO: remove this
    )

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


class CitizenshipDocumentFile(UserUploadedDocumentFile):
    SLUG = "citizenship_document"

    def get_upload_path(self, filename):
        return f"profile/{self.uploaded_by.id}/citizenship_document/{filename}"

    class Meta:
        verbose_name = _("Citizenship Document File")
        verbose_name_plural = _("Citizenship Document Files")


class CanadaVisa(models.Model):
    class Status(models.TextChoices):
        CITIZENSHIP = "citizenship", _("Citizenship")
        PERMANENT_RESIDENT = "permanent_resident", _("Permanent Resident (PR)")
        TEMPORARY_RESIDENT_OPEN_WORK_PERMIT = (
            "temporary_resident_open_work_permit",
            _("Temporary Resident (Open Work Permit)"),
        )
        TEMPORARY_RESIDENT_CLOSE_WORK_PERMIT = (
            "temporary_resident_close_work_permit",
            _("Temporary Resident (Close Work Permit)"),
        )
        TEMPORARY_RESIDENT_STUDY_PERMIT = "temporary_resident_study_permit", _("Temporary Resident (Study Permit)")
        REFUGEE_WORK_PERMIT = "refugee_work_permit", _("Refugee (Work Permit)")
        SEASONAL_AGRICULTURAL_WORKER_PROGRAM = (
            "seasonal_agricultural_worker_program",
            _("Seasonal Agricultural Worker Program (SAWP)"),
        )
        INTERNATIONAL_EXPERIENCE_CANADA = "international_experience_canada", _("International Experience Canada (IEC)")
        ELECTRONIC_TRAVEL_AUTHORIZATION = "electronic_travel_authorization", _("Electronic Travel Authorization (eTA)")
        VISITOR_VISA = "visitor_visa", _("Visitor Visa")

    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name=_("User"), related_name="canada_visa")
    nationality = models.ForeignKey(
        Country, on_delete=models.CASCADE, verbose_name=_("Nationality"), related_name="canada_visas"
    )
    status = models.CharField(
        max_length=50,
        choices=Status.choices,
        verbose_name=_("Status"),
    )

    citizenship_document_x = models.OneToOneField(
        CitizenshipDocumentFile,
        on_delete=models.CASCADE,
        related_name="canada_visa_x",
        verbose_name=_("Citizenship Document"),
        null=True,  # TODO: remove this
        default=None,  # TODO: remove this
    )

    citizenship_document = models.FileField(
        upload_to=citizenship_document_path,
        verbose_name=_("Citizenship Document"),
        validators=[DOCUMENT_FILE_EXTENSION_VALIDATOR, DOCUMENT_FILE_SIZE_VALIDATOR],
    )

    class Meta:
        verbose_name = _("Canada Visa")
        verbose_name_plural = _("Canada Visas")


class ResumeFile(UserUploadedDocumentFile):
    SLUG = "resume"

    def get_upload_path(self, filename):
        return f"profile/{self.uploaded_by.id}/resume/{filename}"

    class Meta:
        verbose_name = _("Resume File")
        verbose_name_plural = _("Resume Files")


class Resume(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name=_("User"), related_name="resume")
    file_x = models.OneToOneField(
        ResumeFile,
        on_delete=models.CASCADE,
        related_name="resume_x",
        verbose_name=_("Resume"),
        null=True,  # TODO: remove this
        blank=True,
        default=None,  # TODO: remove this
    )

    file = models.FileField(
        upload_to=resume_path,
        verbose_name=_("Resume"),
        validators=[DOCUMENT_FILE_EXTENSION_VALIDATOR, DOCUMENT_FILE_SIZE_VALIDATOR],
    )
    text = models.TextField(verbose_name=_("Resume Text"), blank=True, null=True)
    resume_json = models.JSONField(verbose_name=_("Resume JSON"), default=dict)

    class Meta:
        verbose_name = _("Resume")
        verbose_name_plural = _("Resumes")

    def __str__(self):
        return self.user.email


class Referral(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="referral")
    code = models.CharField(max_length=20, unique=True, default=generate_unique_referral_code)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["code"]),
        ]

    def __str__(self):
        return self.code


class ReferralUser(models.Model):
    referral = models.ForeignKey(Referral, on_delete=models.CASCADE, related_name="referred_users")
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="referral_source")
    referred_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("referral", "user")

    def __str__(self):
        return f"{self.referral.code} - {self.user.email}"


class SupportTicket(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", _("Open")
        CLOSED = "closed", _("Closed")

    class Priority(models.TextChoices):
        LOW = "low", _("Low")
        MEDIUM = "medium", _("Medium")
        HIGH = "high", _("High")
        URGENT = "urgent", _("Urgent")

    class Category(models.TextChoices):
        PROFILE = "profile", _("Profile")
        RESUME = "resume", _("Resume")
        JOB_INTEREST = "job_interest", _("Job Interest")
        ACADEMY = "academy", _("Academy")

    class ContactMethod(models.TextChoices):
        EMAIL = "email", _("Email")
        PHONE = "phone", _("Phone")
        WHATSAPP = "whatsapp", _("WhatsApp")

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="support_tickets")
    ticket_id = models.CharField(max_length=255, unique=True, editable=False, default=generate_ticket_id)
    title = models.CharField(max_length=255)
    description = models.TextField(max_length=1024)
    status = models.CharField(max_length=50, choices=Status.choices, default=Status.OPEN)
    priority = models.CharField(max_length=50, choices=Priority.choices)
    category = models.CharField(max_length=50, choices=Category.choices)
    contact_method = models.CharField(max_length=50, choices=ContactMethod.choices)
    contact_value = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Support Ticket")
        verbose_name_plural = _("Support Tickets")

    def __str__(self):
        return self.title


class UserTask(models.Model):
    class TaskStatus(models.TextChoices):
        SCHEDULED = "scheduled", _("Scheduled")
        IN_PROGRESS = "in_progress", _("In Progress")
        COMPLETED = "completed", _("Completed")
        FAILED = "failed", _("Failed")

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tasks")
    task_name = models.CharField(max_length=255, choices=[(i, i) for i in task_registry.get_all_tasks()])
    status = models.CharField(max_length=50, choices=TaskStatus.choices, default=TaskStatus.SCHEDULED)

    def change_status(self, status: str):
        self.status = status
        self.save(update_fields=[UserTask.status.field.name])
        return

    def __str__(self):
        return f"{self.user} - {self.task_name}"

    class Meta:
        verbose_name = _("User Task")
        verbose_name_plural = _("User Tasks")
        unique_together = [("user", "task_name")]
