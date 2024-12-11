import base64
import contextlib
import random
import re
import string
import uuid
from operator import attrgetter
from typing import Dict, List, Optional, Union

from cities_light.models import City, Country
from colorfield.fields import ColorField
from common.choices import LANGUAGES
from common.exceptions import GraphQLErrorBadRequest
from common.mixins import HasDurationMixin
from common.models import (
    Field,
    FileModel,
    Industry,
    Job,
    JobBenefit,
    LanguageProficiencySkill,
    LanguageProficiencyTest,
    Skill,
    SlugTitleAbstract,
    University,
)
from common.states import ChangeStateMixin, GenericState
from common.utils import field_serializer, fj, get_all_subclasses
from common.validators import (
    DOCUMENT_FILE_EXTENSION_VALIDATOR,
    DOCUMENT_FILE_SIZE_VALIDATOR,
    IMAGE_FILE_EXTENSION_VALIDATOR,
    IMAGE_FILE_SIZE_VALIDATOR,
    ValidateFileSize,
)
from computedfields.models import ComputedFieldsModel, computed
from flex_eav.models import EavAttribute, EavValue
from flex_report import report_model
from graphql_jwt.refresh_token.models import RefreshToken
from markdownfield.models import MarkdownField
from markdownfield.validators import VALIDATOR_STANDARD
from model_utils.models import TimeStampedModel
from phonenumber_field.modelfields import PhoneNumberField
from phonenumber_field.phonenumber import PhoneNumber

from django.contrib.auth.models import AbstractUser
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import ArrayField, IntegerRangeField
from django.contrib.postgres.lookups import Overlap
from django.core import checks
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import models, transaction
from django.db.models.constraints import UniqueConstraint
from django.db.models.lookups import (
    Contains,
    Exact,
    GreaterThanOrEqual,
    IExact,
    In,
    IsNull,
    LessThan,
    LessThanOrEqual,
)
from django.http import HttpRequest
from django.template.loader import render_to_string
from django.templatetags.static import static
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

from .choices import (
    ContactType,
    EducationDegree,
    GenderChoices,
    IEEEvaluator,
    UserTaskStatus,
    WorkExperienceGrade,
    get_task_names_choices,
)
from .constants import (
    EARLY_USERS_COUNT,
    ORGANIZATION_PHONE_OTP_CACHE_KEY,
    ORGANIZATION_PHONE_OTP_EXPIRY,
    SUPPORT_RECIPIENT_LIST,
    SUPPORT_TICKET_SUBJECT_TEMPLATE,
    FileSlugs,
    ProfileAnnotationNames,
)
from .managers import (
    CertificateAndLicenseManager,
    FlexReportProfileManager,
    OrganizationInvitationManager,
    ProfileManager,
    UserManager,
)
from .mixins import EmailVerificationMixin
from .validators import (
    BlocklistEmailDomainValidator,
    LinkedInUsernameValidator,
    NameValidator,
    NoTagEmailValidator,
)


def generate_unique_referral_code():
    return base64.b32encode(uuid.uuid4().bytes).decode("utf-8")[:8]


def generate_invitation_token():
    return base64.b32encode(uuid.uuid4().bytes).decode("utf-8")[:15]


def generate_dnc_txt_record_code():
    return base64.b32encode(uuid.uuid4().bytes).decode("utf-8")[:20]


def generate_unique_file_name():
    return "cpj_" + base64.b32encode(uuid.uuid4().bytes).decode("utf-8")[:20]


def generate_unique_verification_code():
    import random

    return random.randint(100000, 999999)


def generate_ticket_id():
    return str(uuid.uuid4())[:8]


def get_phone_otp(length=6):
    return "".join(random.choices(string.digits, k=length))


class Contactable(models.Model):
    def get_related_object(self) -> Union["Organization", "Profile"]:
        return getattr(
            self,
            Profile.contactable.field.related_query_name(),
            Organization.contactable.field.related_query_name(),
        )

    def __str__(self):
        return str(self.get_related_object())

    class Meta:
        verbose_name = _("Contactable")
        verbose_name_plural = _("Contactables")


class Contact(models.Model):
    Type = ContactType

    VALIDATORS = {
        Type.WEBSITE: models.URLField().run_validators,
        Type.ADDRESS: None,
        Type.LINKEDIN: LinkedInUsernameValidator(),
        Type.WHATSAPP: PhoneNumberField().run_validators,
        Type.PHONE: PhoneNumberField().run_validators,
    }

    VALUE_FIXERS = {
        Type.PHONE: lambda value: PhoneNumber.from_string(value).as_e164,
    }

    TYPE_ICON = {
        Type.WEBSITE: static("img/icon/web.svg"),
        Type.ADDRESS: static("img/icon/Building office.svg"),
        Type.LINKEDIN: static("img/icon/linkedin.svg"),
        Type.WHATSAPP: static("img/icon/whatsapp.svg"),
        Type.PHONE: static("img/icon/Call.svg"),
    }

    contactable = models.ForeignKey(
        Contactable,
        on_delete=models.CASCADE,
        verbose_name=_("Contactable"),
        related_name="contacts",
    )
    type = models.CharField(
        max_length=50,
        choices=Type.choices,
        verbose_name=_("Type"),
        default=Type.WEBSITE.value,
    )
    value = models.CharField(max_length=255, verbose_name=_("Value"))

    class Meta:
        unique_together = ("contactable", "type")
        verbose_name = _("Contact")
        verbose_name_plural = _("Contacts")

    def __str__(self):
        return f"{self.contactable} - {self.type}: {self.value}"

    def get_contact_icon(self):
        return self.TYPE_ICON.get(self.type)

    def get_display_name_and_link(self) -> Dict[str, Optional[str]]:
        display_name, link = self.value, None

        match self.type:
            case Contact.Type.WEBSITE:
                display_regex = re.compile(r"(?:https?://)?(?:www\.)?([^/]+)")
                display_name = display_regex.match(self.value).group(1)
                link = self.value

            case Contact.Type.PHONE:
                link = f"tel:{PhoneNumber.from_string(self.value).as_international}"

            case Contact.Type.LINKEDIN:
                display_regex = r"(?:https?://)?(?:www\.)?linkedin\.com/in/([^/]+)"
                display_name = re.match(display_regex, self.value).group(1)
                link = self.value

            case Contact.Type.WHATSAPP:
                link = f"https://wa.me/{self.value.strip('/')}"
                display_regex = r"(?:https?://)?(?:www\.)?wa\.me/([^/]+)"
                display_name = (
                    (matched_value := re.match(display_regex, self.value)) and matched_value.group(1)
                ) or self.value

        return {"display": display_name, "link": link}

    def clean(self, *args, **kwargs):
        if self.type in self.VALIDATORS:
            with contextlib.suppress(TypeError):
                try:
                    self.VALIDATORS[self.type](self.value)
                except ValidationError as e:
                    raise ValidationError(
                        {Contact.value.field.name: list(map(field_serializer(self.type), e.messages))},
                    ) from e
        else:
            raise NotImplementedError(f"Validation for {self.type} is not implemented")

        if self.type in self.VALUE_FIXERS:
            self.value = self.VALUE_FIXERS[self.type](self.value)


class User(AbstractUser):
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    FIELDS_PROPERTIES = {
        "email": {
            "_unique": True,
            "blank": False,
            "null": False,
            "db_index": True,
            "validators": [NoTagEmailValidator(), BlocklistEmailDomainValidator()],
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

    objects = UserManager()

    class RegistrationType(models.TextChoices):
        JOB_SEEKER = "job_seeker", _("Job Seeker")
        ORGANIZATION = "organization", _("Organization")

    registration_type = models.CharField(
        max_length=50,
        choices=RegistrationType.choices,
        default=RegistrationType.JOB_SEEKER.value,
        verbose_name=_("Registration Type"),
    )

    def get_profile(self) -> "Profile":
        return (
            (profile := getattr(self, Profile.user.field.related_query_name(), None))
            and getattr(profile, "pk")
            and profile
        )

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    full_name.fget.verbose_name = _("Full Name")

    @property
    def has_resume(self):
        for field in self.get_resume_related_models():
            field_name = field.field.related_query_name()
            with contextlib.suppress(field.field.model.DoesNotExist):
                value = getattr(self, field_name)
                if value is not None and (isinstance(value, models.Model) or value.exists()):
                    return True
        if self.profile.gender:
            return True
        return False

    def get_resume_related_models(self):
        return (
            Resume.user,
            Education.user,
            WorkExperience.user,
            LanguageCertificate.user,
            CertificateAndLicense.user,
        )

    def has_access(self, access_slug: str):
        return (
            self.is_superuser
            or User.objects.filter(
                models.Q(
                    **{
                        fj(
                            Profile.user.field.related_query_name(),
                            Profile.role,
                            Role.accesses,
                            Access.slug,
                        ): access_slug
                    }
                )
                | models.Q(
                    **{
                        fj(
                            OrganizationMembership.user.field.related_query_name(),
                            OrganizationMembership.role,
                            Role.accesses,
                            Access.slug,
                        ): access_slug
                    }
                ),
                pk=self.pk,
            ).exists()
        )

    def get_contacts_by_type(self, contact_type: Contact.Type, *, include_organization: bool = False) -> List[Contact]:
        profile_contacts = Contact.objects.filter(
            **{
                fj(
                    Contact.contactable,
                    Profile.contactable.field.related_query_name(),
                    Profile.user,
                ): self
            }
        )

        organization_contacts = (
            Contact.objects.filter(
                **{
                    fj(Contact.contactable, In.lookup_name): Contactable.objects.filter(
                        **{
                            fj(Organization.contactable, In.lookup_name): getattr(
                                self, Organization.user.field.related_query_name()
                            ).all()
                        }
                    )
                }
            )
            if include_organization
            else Contact.objects.none()
        )

        return (
            (profile_contacts | organization_contacts)
            .filter(**{Contact.type.field.name: contact_type, fj(Contact.value, IsNull.lookup_name): False})
            .distinct()
        )


for field, properties in User.FIELDS_PROPERTIES.items():
    for key, value in properties.items():
        setattr(User._meta.get_field(field), key, value)


class UserDevice(TimeStampedModel):
    device_id = models.CharField(max_length=255, verbose_name=_("Device ID"), unique=True, db_index=True)
    refresh_token = models.OneToOneField(RefreshToken, on_delete=models.CASCADE, verbose_name=_("Refresh Token"))

    class Meta:
        verbose_name = _("User Device")
        verbose_name_plural = _("User Devices")
        unique_together = ("device_id", "refresh_token")

    @property
    def user(self):
        return self.refresh_token.user

    def __str__(self):
        return f"{self.user} - {self.device_id[:3]}...{self.device_id[-3:]}"


class Access(SlugTitleAbstract):
    class Meta:
        verbose_name = _("Access")
        verbose_name_plural = _("Accesses")
        ordering = ["slug"]


class Role(SlugTitleAbstract):
    description = models.TextField(verbose_name=_("Description"), blank=True, null=True)
    accesses = models.ManyToManyField(Access, verbose_name=_("Accesses"), through="RoleAccess", blank=True)

    managed_by_model = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        verbose_name=_("Managed By Model"),
        related_name="roles",
        blank=True,
        null=True,
    )
    managed_by_id = models.PositiveIntegerField(
        verbose_name=_("Managed By ID"),
        null=True,
        blank=True,
    )
    managed_by = GenericForeignKey("managed_by_model", "managed_by_id")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = _("Role")
        verbose_name_plural = _("Roles")
        ordering = ["title"]


class RoleAccess(models.Model):
    role = models.ForeignKey(
        Role,
        to_field=Role.slug.field.name,
        on_delete=models.CASCADE,
        verbose_name=_("Role"),
    )
    access = models.ForeignKey(
        Access,
        to_field=Access.slug.field.name,
        on_delete=models.CASCADE,
        verbose_name=_("Access"),
    )

    class Meta:
        verbose_name = _("Role Access")
        verbose_name_plural = _("Role Accesses")
        unique_together = ("role", "access")


class UserFile(FileModel):
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="%(class)s")

    class Meta:
        abstract = True

    def check_auth(self, request):
        return request.user == self.uploaded_by

    @classmethod
    def get_user_temporary_file(cls, user: User) -> Optional["UserFile"]:
        return cls.objects.filter(
            **{fj(cls.uploaded_by): user},
            **{field.field.related_query_name(): None for field in cls.get_related_fields()},
        ).first()

    @classmethod
    def is_used(cls, user: User) -> bool:
        return (
            cls.objects.filter(**{fj(cls.uploaded_by): user})
            .exclude(**{field.field.related_query_name(): None for field in cls.get_related_fields()})
            .exists()
        )

    @classmethod
    @transaction.atomic
    def create_temporary_file(cls, file: InMemoryUploadedFile, user: User):
        obj = cls(**{fj(cls.uploaded_by): user, fj(cls.file): file})
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

    def check_auth(self, request: HttpRequest):
        if not request.user.is_authenticated:
            return False

        return (
            super().check_auth(request)
            or OrganizationEmployee.objects.filter(
                **{
                    fj(OrganizationEmployee.user): self.uploaded_by,
                    fj(
                        OrganizationEmployee.organization,
                        OrganizationMembership.organization.field.related_query_name(),
                        OrganizationMembership.user,
                    ): request.user,
                }
            ).exists()
        )


class UserUploadedImageFile(UserFile):
    class Meta:
        abstract = True

    def get_validators(self):
        return [IMAGE_FILE_EXTENSION_VALIDATOR, IMAGE_FILE_SIZE_VALIDATOR]


class AvatarFile(UserUploadedImageFile):
    SLUG = FileSlugs.AVATAR.value

    def get_upload_path(self, filename):
        return f"profile/{self.uploaded_by.id}/avatar/{filename}"

    def get_validators(self):
        return [IMAGE_FILE_EXTENSION_VALIDATOR, ValidateFileSize(max=10)]

    def check_auth(self, request):
        if not request.user.is_authenticated:
            return False

        return (
            super().check_auth(request)
            or JobPositionAssignment.objects.filter(
                **{
                    fj(JobPositionAssignment.job_seeker): self.uploaded_by,
                    fj(
                        JobPositionAssignment.job_position,
                        OrganizationJobPosition.organization,
                        OrganizationMembership.organization.field.related_query_name(),
                        OrganizationMembership.user,
                    ): request.user,
                }
            ).exists()
        )

    class Meta:
        verbose_name = _("Avatar Image")
        verbose_name_plural = _("Avatar Images")


class FullBodyImageFile(UserUploadedImageFile):
    SLUG = FileSlugs.FULL_BODY_IMAGE.value

    def get_upload_path(self, filename):
        return f"profile/{self.uploaded_by.id}/full_body_image/{filename}"

    class Meta:
        verbose_name = _("Full Body Image")
        verbose_name_plural = _("Full Body Images")


@report_model.register
class Profile(ComputedFieldsModel):
    Gender = GenderChoices

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

    contactable = models.OneToOneField(
        Contactable,
        on_delete=models.SET_NULL,
        verbose_name=_("Contactable"),
        null=True,
        blank=True,
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name=_("User"))
    height = models.IntegerField(null=True, blank=True)
    weight = models.IntegerField(null=True, blank=True)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, verbose_name=_("Role"), null=True, blank=True)
    skin_color = ColorField(choices=SkinColor.choices, null=True, blank=True, verbose_name=_("Skin Color"))
    hair_color = ColorField(null=True, blank=True, verbose_name=_("Hair Color"))
    eye_color = ColorField(choices=EyeColor.choices, null=True, blank=True, verbose_name=_("Eye Color"))
    avatar = models.OneToOneField(
        AvatarFile,
        on_delete=models.SET_NULL,
        related_name="profile",
        null=True,
        blank=True,
        verbose_name=_("Avatar"),
    )
    full_body_image = models.OneToOneField(
        FullBodyImageFile,
        on_delete=models.SET_NULL,
        related_name="profile",
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
    job_type_exclude = ArrayField(
        models.CharField(max_length=50, choices=JobType.choices),
        verbose_name=_("Job Type Exclude"),
        null=True,
        blank=True,
    )
    job_location_type_exclude = ArrayField(
        models.CharField(max_length=50, choices=JobLocationType.choices),
        verbose_name=_("Job Location Type Exclude"),
        null=True,
        blank=True,
    )
    scores = models.JSONField(verbose_name=_("Scores"), default=dict, blank=True)
    score = models.PositiveIntegerField(verbose_name=_("Score"), default=0, blank=True)
    gender = models.CharField(
        max_length=50,
        choices=Gender.choices,
        verbose_name=_("Gender"),
        null=True,
        blank=True,
    )
    birth_date = models.DateField(verbose_name=_("Birth Date"), null=True, blank=True)
    raw_skills = ArrayField(models.CharField(max_length=64), verbose_name=_("Raw Skills"), blank=True, null=True)
    skills = models.ManyToManyField(Skill, verbose_name=_("Skills"), related_name="profiles", blank=True)
    available_jobs = models.ManyToManyField(Job, verbose_name=_("Available Jobs"), related_name="profiles", blank=True)
    allow_notifications = models.BooleanField(default=True, verbose_name=_("Allow Notifications"))
    accept_terms_and_conditions = models.BooleanField(default=False, verbose_name=_("Accept Terms"))

    objects = ProfileManager()
    flex_report_custom_manager = FlexReportProfileManager()

    @computed(
        models.IntegerField(verbose_name=_("Credits")),
        depends=[
            ("user.referral.referred_users.user.status", ["verified"]),
        ],
    )
    def credits(self):
        from graphql_auth.models import UserStatus

        _credits = 0
        early_users_pks = User.objects.order_by(fj(User.date_joined))[:EARLY_USERS_COUNT].values_list(
            User._meta.pk.attname,
            flat=True,
        )
        is_early_user = (
            User.objects.filter(**{fj(User._meta.pk.attname, In.lookup_name): early_users_pks})
            .filter(**{fj(self._meta.pk.attname): self.user.pk})
            .exists()
        )

        with contextlib.suppress(ObjectDoesNotExist):
            verified_referrals = ReferralUser.objects.filter(
                **{
                    fj(ReferralUser.referral, Referral.user): self.user,
                    fj(
                        ReferralUser.user,
                        UserStatus.user.field.related_query_name(),
                        UserStatus.verified,
                    ): True,
                }
            )
            _credits += verified_referrals.count() * (150 if is_early_user else 100)

        return _credits

    @property
    def completion_percentage(self):
        related_scores = self.get_completion_related_scores()
        scores = self.scores
        completed_scores = sum(1 for score in related_scores if scores.get(score.slug, 0))
        return (completed_scores / len(related_scores)) * 100

    completion_percentage.fget.verbose_name = _("Completion Percentage")

    class Meta:
        verbose_name = _("User Profile")
        verbose_name_plural = _("User Profiles")

    def __str__(self):
        return self.user.email

    @classmethod
    def flex_report_search_fields(cls):
        return {
            cls.native_language.field.name: [Exact.lookup_name],
            cls.birth_date.field.name: [GreaterThanOrEqual.lookup_name, LessThanOrEqual.lookup_name],
            fj(cls.user, User.email): [IExact.lookup_name],
            fj(cls.user): [In.lookup_name],
            cls.gender.field.name: [Exact.lookup_name],
            cls.interested_jobs.field.name: [Contains.lookup_name],
            fj(cls.city, City.country): [In.lookup_name, IExact.lookup_name],
            ProfileAnnotationNames.AGE: [
                GreaterThanOrEqual.lookup_name,
                LessThanOrEqual.lookup_name,
                Exact.lookup_name,
            ],
            ProfileAnnotationNames.IS_ORGANIZATION_MEMBER: [Exact.lookup_name],
            ProfileAnnotationNames.HAS_EDUCATION: [Exact.lookup_name],
            ProfileAnnotationNames.HAS_UNVERIFIED_EDUCATION: [Exact.lookup_name],
            ProfileAnnotationNames.HAS_WORK_EXPERIENCE: [Exact.lookup_name],
            ProfileAnnotationNames.HAS_UNVERIFIED_WORK_EXPERIENCE: [Exact.lookup_name],
            ProfileAnnotationNames.HAS_CERTIFICATE: [Exact.lookup_name],
            ProfileAnnotationNames.HAS_LANGUAGE_CERTIFICATE: [Exact.lookup_name],
            ProfileAnnotationNames.HAS_CANADA_VISA: [Exact.lookup_name],
            ProfileAnnotationNames.DATE_JOINED: [GreaterThanOrEqual.lookup_name, LessThanOrEqual.lookup_name],
            ProfileAnnotationNames.LAST_LOGIN: [GreaterThanOrEqual.lookup_name, LessThanOrEqual.lookup_name],
            ProfileAnnotationNames.COMPLETED_STAGES: [Overlap.lookup_name],
            ProfileAnnotationNames.INCOMPLETE_STAGES: [Overlap.lookup_name],
            ProfileAnnotationNames.HAS_PROFILE_INFORMATION: [Exact.lookup_name],
            ProfileAnnotationNames.HAS_RESUME: [Exact.lookup_name],
            ProfileAnnotationNames.HAS_INTERESTED_JOBS: [Exact.lookup_name],
        }

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

    has_appearance_related_data.fget.verbose_name = _("Has Appearance Related Data")

    @property
    def job_type(self):
        return (
            Profile.objects.filter(**{Profile._meta.pk.attname: self.pk})
            .values_list(Profile.job_type.fget.annotation_name, flat=True)
            .first()
        )

    @job_type.setter
    def job_type(self, value: List[JobType]):
        self.job_type_exclude = list(set(Profile.JobType.values) - set(map(attrgetter("value"), value)))

    job_type.fget.annotation_name = f"{job_type.fget.__name__}_annotation"

    @property
    def job_location_type(self):
        return (
            Profile.objects.filter(**{Profile._meta.pk.attname: self.pk})
            .values_list(Profile.job_location_type.fget.annotation_name, flat=True)
            .first()
        )

    @job_location_type.setter
    def job_location_type(self, value: List[JobLocationType]):
        self.job_location_type_exclude = list(
            set(Profile.JobLocationType.values) - set(map(attrgetter("value"), value))
        )

    job_location_type.fget.annotation_name = f"{job_location_type.fget.__name__}_annotation"


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
        return (cls.Status.VERIFIED, cls.Status.SELF_VERIFIED)


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

    def after_create(self, request):
        pass

    def clean(self, *args, **kwargs):
        document = self.get_document()
        if (methods := list(document.get_verification_methods())) and len(methods) > 1:
            raise ValidationError(f"{document._meta.verbose_name} already has a verification method")


class Education(DocumentAbstract, HasDurationMixin):
    Degree = EducationDegree

    field = models.ForeignKey(Field, on_delete=models.RESTRICT, verbose_name=_("Field"))
    degree = models.CharField(max_length=50, choices=Degree.choices, verbose_name=_("Degree"))
    university = models.ForeignKey(University, on_delete=models.RESTRICT, verbose_name=_("University"))
    city = models.ForeignKey(City, on_delete=models.RESTRICT, verbose_name=_("City"))
    start = models.DateField(verbose_name=_("Start Date"))
    end = models.DateField(verbose_name=_("End Date"), null=True, blank=True)

    class Meta:
        verbose_name = _("Education")
        verbose_name_plural = _("Educations")
        ordering = [
            "end",
            "start",
        ]

    @property
    def title(self):
        return f"{self.get_degree_display()} in {self.field.name}"

    title.fget.verbose_name = _("Title")

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
    SLUG = FileSlugs.EDUCATION_EVALUATION.value

    def get_upload_path(self, filename):
        return f"profile/{self.uploaded_by.id}/education_verification/education_evaluation/{filename}"

    class Meta:
        verbose_name = _("Education Evaluation Document File")
        verbose_name_plural = _("Education Evaluation Document Files")


class IEEMethod(EducationVerificationMethodAbstract):
    Evaluator = IEEEvaluator

    education_evaluation_document = models.OneToOneField(
        EducationEvaluationDocumentFile,
        on_delete=models.CASCADE,
        related_name="iee_method",
        verbose_name=_("Education Evaluation Document"),
    )
    evaluator = models.CharField(
        max_length=50,
        choices=Evaluator.choices,
        verbose_name=_("Academic Credential Evaluator"),
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = _("International Education Evaluation Method")
        verbose_name_plural = _("International Education Evaluation Methods")


class DegreeFile(UserUploadedDocumentFile):
    SLUG = FileSlugs.DEGREE.value

    def get_upload_path(self, filename):
        return f"profile/{self.uploaded_by.id}/education_verification/degree/{filename}"

    class Meta:
        verbose_name = _("Degree File")
        verbose_name_plural = _("Degree Files")


class CommunicationMethod(EducationVerificationMethodAbstract, EmailVerificationMixin):
    _verification_template_name = "email/verification/education.html"
    _verification_subject = "Request for Educational Credential Verification"

    website = models.URLField(verbose_name=_("Website"))
    email = models.EmailField(verbose_name=_("Email"))
    department = models.CharField(max_length=255, verbose_name=_("Department"))
    person = models.CharField(max_length=255, verbose_name=_("Person"))
    degree_file = models.OneToOneField(
        DegreeFile,
        on_delete=models.CASCADE,
        related_name="communication_method",
        verbose_name=_("Degree File"),
    )

    def get_file_model_ids(self):
        return [self.degree_file.pk]

    def get_verification_context_data(self, **kwargs):
        return super().get_verification_context_data(**kwargs, education=self.education)

    class Meta:
        verbose_name = _("Communication Method")
        verbose_name_plural = _("Communication Methods")


class WorkExperience(DocumentAbstract, HasDurationMixin):
    Grade = WorkExperienceGrade

    job_title = models.CharField(max_length=255, verbose_name=_("Job Title"))
    grade = models.CharField(max_length=50, choices=Grade.choices, verbose_name=_("Grade"))
    start = models.DateField(verbose_name=_("Start Date"))
    end = models.DateField(verbose_name=_("End Date"), null=True, blank=True)
    organization = models.CharField(max_length=255, verbose_name=_("Organization"))
    city = models.ForeignKey(City, on_delete=models.RESTRICT, verbose_name=_("City"), related_name="work_experiences")
    industry = models.ForeignKey(Industry, on_delete=models.RESTRICT, verbose_name=_("Industry"))
    skills = models.CharField(max_length=250, verbose_name=_("Skills"), blank=True, null=True)

    class Meta:
        verbose_name = _("Work Experience")
        verbose_name_plural = _("Work Experiences")
        ordering = [
            "end",
            "start",
        ]

    def __str__(self):
        return f"{self.user.email} - {self.job_title} - {self.organization}"

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
    SLUG = FileSlugs.EMPLOYER_LETTER.value

    def get_upload_path(self, filename):
        return f"profile/{self.uploaded_by.id}/work_experience_verification/employer_letter/{filename}"

    class Meta:
        verbose_name = _("Employer Letter File")
        verbose_name_plural = _("Employer Letter Files")


class EmployerLetterMethod(WorkExperienceVerificationMethodAbstract, EmailVerificationMixin):
    employer_letter = models.OneToOneField(
        EmployerLetterFile,
        on_delete=models.CASCADE,
        related_name="employer_letter_method",
        verbose_name=_("Employer Letter"),
    )

    def send_verification(self, *, is_async=True):
        for employer in self.employers.all():
            employer.send_verification(is_async=is_async)

    class Meta:
        verbose_name = _("Employer Letter Method")
        verbose_name_plural = _("Employer Letter Methods")


class PaystubsFile(UserUploadedDocumentFile):
    SLUG = FileSlugs.PAYSTUBS.value

    def get_upload_path(self, filename):
        return f"profile/{self.uploaded_by.id}/work_experience_verification/paystubs/{filename}"

    class Meta:
        verbose_name = _("Paystubs File")
        verbose_name_plural = _("Paystubs Files")


class PaystubsMethod(WorkExperienceVerificationMethodAbstract):
    paystubs = models.OneToOneField(
        PaystubsFile,
        on_delete=models.CASCADE,
        related_name="paystubs_method",
        verbose_name=_("Paystubs"),
    )

    class Meta:
        verbose_name = _("Paystubs Method")
        verbose_name_plural = _("Paystubs Methods")


class ReferenceCheckEmployer(models.Model, EmailVerificationMixin):
    _verification_template_name = "email/verification/work_experience.html"
    _verification_subject = "Request for Employment Verification"

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

    def get_verification_context_data(self, **kwargs):
        return super().get_verification_context_data(
            **kwargs,
            employer=self.name,
            work_experience=self.work_experience_verification.work_experience,
        )

    def get_file_model_ids(self):
        return [self.work_experience_verification.employer_letter.pk]

    class Meta:
        verbose_name = _("Reference Check Employer")
        verbose_name_plural = _("Reference Check Employers")

    def __str__(self):
        return f"{self.work_experience_verification} - {self.name}"


class LanguageCertificate(DocumentAbstract, HasDurationMixin):
    start_date_field = "issued_at"
    end_date_field = "expired_at"

    language = models.CharField(choices=LANGUAGES, max_length=32, verbose_name=_("Language"))
    test = models.ForeignKey(
        LanguageProficiencyTest,
        on_delete=models.RESTRICT,
        verbose_name=_("Test"),
        related_name="certificates",
    )
    issued_at = models.DateField(verbose_name=_("Issued At"))
    expired_at = models.DateField(verbose_name=_("Expired At"), null=True, blank=True)

    @property
    def scores(self):
        return ", ".join(
            f"{skill}: {score}"
            for skill, score in self.values.values_list(
                fj(LanguageCertificateValue.skill, LanguageProficiencySkill.skill_name),
                fj(LanguageCertificateValue.value),
            )
        )

    scores.fget.verbose_name = _("Scores")

    def __str__(self):
        return f"{self.user.email} - {self.language}"

    class Meta:
        verbose_name = _("Language Certificate")
        verbose_name_plural = _("Language Certificates")

    @classmethod
    def get_verification_abstract_model(cls):
        return LanguageCertificateVerificationMethodAbstract

    def clean(self):
        if self.expired_at and self.issued_at > self.expired_at:
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
        if not self.skill.test == self.language_certificate.test:
            raise ValidationError({LanguageCertificateValue.skill.field.name: _("Skill must be related to the test")})
        try:
            super().clean()
        except ValidationError as e:
            message = ""

            error = getattr(e, "error_dict", None) or getattr(e, "error_list", None)
            if error:
                message = list(
                    map(
                        field_serializer(self.skill.skill_name, self.skill.pk),
                        map(attrgetter("message"), error.values() if isinstance(error, dict) else error),
                    )
                )

            raise ValidationError({LanguageCertificateValue.value.field.name: message})


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
    SLUG = FileSlugs.LANGUAGE_CERTIFICATE.value

    def get_upload_path(self, filename):
        return f"profile/{self.uploaded_by.id}/language_certificate_verification/language_certificate/{filename}"

    class Meta:
        verbose_name = _("Language Certificate File")
        verbose_name_plural = _("Language Certificate Files")


class OfflineMethod(LanguageCertificateVerificationMethodAbstract):
    certificate_file = models.OneToOneField(
        LanguageCertificateFile,
        on_delete=models.CASCADE,
        related_name="offline_method",
        verbose_name=_("Language Certificate"),
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
    certificate_text = models.TextField(verbose_name=_("Certificate Text"), blank=True, null=True)
    certifier = models.CharField(max_length=255, verbose_name=_("Certifier"))
    issued_at = models.DateField(verbose_name=_("Issued At"))
    expired_at = models.DateField(verbose_name=_("Expired At"), null=True, blank=True)

    objects = CertificateAndLicenseManager()

    class Meta:
        verbose_name = _("Certificate And License")
        verbose_name_plural = _("Certificates And Licenses")
        ordering = [
            "issued_at",
        ]

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
    SLUG = FileSlugs.CERTIFICATE.value

    def get_upload_path(self, filename):
        return f"profile/{self.uploaded_by.id}/certificate_and_license_verification/certificate_and_license/{filename}"

    class Meta:
        verbose_name = _("Certificate File")
        verbose_name_plural = _("Certificate Files")


class CertificateAndLicenseOfflineVerificationMethod(CertificateAndLicenseVerificationMethodAbstract):
    certificate_file = models.OneToOneField(
        CertificateFile,
        on_delete=models.CASCADE,
        related_name="offline_method",
        verbose_name=_("Certificate And License"),
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
    SLUG = FileSlugs.CITIZENSHIP_DOCUMENT.value

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
        Country, on_delete=models.RESTRICT, verbose_name=_("Nationality"), related_name="canada_visas"
    )
    status = models.CharField(
        max_length=50,
        choices=Status.choices,
        verbose_name=_("Status"),
    )

    citizenship_document = models.OneToOneField(
        CitizenshipDocumentFile,
        on_delete=models.CASCADE,
        related_name="canada_visa",
        verbose_name=_("Citizenship Document"),
    )

    class Meta:
        verbose_name = _("Canada Visa")
        verbose_name_plural = _("Canada Visas")


class ResumeFile(UserUploadedDocumentFile):
    SLUG = FileSlugs.RESUME.value

    def get_upload_path(self, filename):
        return f"profile/{self.uploaded_by.id}/resume/{filename}"

    def check_auth(self, request):
        return (
            super().check_auth(request)
            or JobPositionAssignment.objects.filter(
                **{
                    fj(
                        JobPositionAssignment.job_position,
                        OrganizationJobPosition.organization,
                        OrganizationMembership.organization.field.related_query_name(),
                        OrganizationMembership.user,
                    ): request.user,
                }
            ).exists()
        )

    class Meta:
        verbose_name = _("Resume File")
        verbose_name_plural = _("Resume Files")


class Resume(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name=_("User"), related_name="resume")
    file = models.OneToOneField(
        ResumeFile,
        on_delete=models.CASCADE,
        related_name="resume",
        verbose_name=_("Resume"),
    )
    resume_json = models.JSONField(verbose_name=_("Resume JSON"), default=dict, blank=True, null=True)

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


class SupportTicketCategory(models.Model):
    class Type(models.TextChoices):
        ORGANIZATION = "organization", _("Organization")
        JOB_SEEKER = "job_seeker", _("Job Seeker")

    title = models.CharField(max_length=255, verbose_name=_("Title"), unique=True)
    types = ArrayField(
        models.CharField(max_length=50, choices=Type.choices),
        verbose_name=_("Types"),
    )

    class Meta:
        verbose_name = _("Support Ticket Category")
        verbose_name_plural = _("Support Ticket Categories")
        ordering = [
            "title",
        ]

    def __str__(self):
        return self.title


class SupportTicket(TimeStampedModel):
    class Status(models.TextChoices):
        OPEN = "open", _("Open")
        CLOSED = "closed", _("Closed")

    class Priority(models.TextChoices):
        LOW = "low", _("Low")
        MEDIUM = "medium", _("Medium")
        HIGH = "high", _("High")
        URGENT = "urgent", _("Urgent")

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
    category = models.ForeignKey(
        SupportTicketCategory,
        on_delete=models.CASCADE,
        related_name="support_tickets",
        verbose_name=_("Category"),
    )
    contact_method = models.CharField(max_length=50, choices=ContactMethod.choices)
    contact_value = models.CharField(max_length=255)

    def notify_open(self):
        from .tasks import send_email_async

        template_name = "email/support_ticket/open.html"
        context = {"ticket": self}
        content = render_to_string(template_name, context)

        send_email_async.delay(
            recipient_list=SUPPORT_RECIPIENT_LIST,
            from_email=None,
            content=content,
            subject=SUPPORT_TICKET_SUBJECT_TEMPLATE % {"ticket_id": self.ticket_id},
        )

    def notify(self):
        if not (
            notify_callback := {
                self.Status.OPEN: self.notify_open,
            }.get(self.status)
        ):
            return

        notify_callback()

    class Meta:
        verbose_name = _("Support Ticket")
        verbose_name_plural = _("Support Tickets")

    def __str__(self):
        return self.title


class UserTask(TimeStampedModel):
    Status = UserTaskStatus

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tasks")
    task_name = models.CharField(
        max_length=255,
        choices=get_task_names_choices,
        verbose_name=_("Task Name"),
    )
    status = models.CharField(max_length=50, choices=Status.choices, blank=True, null=True, verbose_name=_("Status"))
    status_description = models.TextField(verbose_name=_("Status Description"), blank=True, null=True)

    def change_status(self, status: str, description: str = None):
        self.status = status
        self.status_description = description
        self.save(
            update_fields=[
                UserTask.status.field.name,
                UserTask.status_description.field.name,
            ]
        )

    def __str__(self):
        return f"{self.user} - {self.task_name}"

    class Meta:
        verbose_name = _("User Task")
        verbose_name_plural = _("User Tasks")
        constraints = [
            UniqueConstraint(
                fields=["user", "task_name"],
                condition=models.Q(
                    status__in=[
                        UserTaskStatus.SCHEDULED,
                        UserTaskStatus.IN_PROGRESS,
                    ]
                ),
                name="unique_user_task_name_scheduled_or_in_progress",
            ),
        ]
        ordering = ["-created", "task_name"]


class OrganizationLogoFile(UserUploadedImageFile):
    SLUG = FileSlugs.ORGANIZATION_LOGO.value

    def get_upload_path(self, filename):
        return f"organization/logo/{self.uploaded_by.id}/{filename}"

    class Meta:
        verbose_name = _("Organization Logo File")
        verbose_name_plural = _("Organization Logo Files")


class Organization(DocumentAbstract):
    class Status(models.TextChoices):
        DRAFTED = "drafted", _("Drafted")
        SUBMITTED = "submitted", _("Submitted")
        REJECTED = "rejected", _("Rejected")
        VERIFIED = "verified", _("Verified")

    class Type(models.TextChoices):
        SOLE_PROPRIETORSHIP = "sole_proprietorship", _("Sole Proprietorship")
        GENERAL_PARTNERSHIP = "general_partnership", _("General Partnership")
        LIMITED_PARTNERSHIP = "limited_partnership", _("Limited Partnership")
        PRIVATE_CORPORATION = "private_corporation", _("Private Corporation")
        PUBLIC_CORPORATION = "public_corporation", _("Public Corporation")
        COOPERATIVE = "cooperative", _("Cooperative")
        NON_PROFIT_ORGANIZATION = "non_profit_organization", _("Non-Profit Organization")
        BRANCH_OFFICE = "branch_office", _("Branch Office")
        SUBSIDIARY = "subsidiary", _("Subsidiary")

    class BussinessType(models.TextChoices):
        SOFTWARE = "software", _("Software")
        SERVICE = "service", _("Service")
        PRODUCT = "product", _("Product")

    class Size(models.TextChoices):
        _1_10 = "_1_10", _("1-10")
        _10_50 = "_10_50", _("10-50")
        _50_100 = "_50_100", _("50-100")
        _100_500 = "_100_500", _("100-500")
        _500_1000 = "_500_1000", _("500-1000")
        OVER_1000 = "over_1000", _("Over 1000")

    contactable = models.OneToOneField(
        Contactable,
        on_delete=models.SET_NULL,
        verbose_name=_("Contactable"),
        null=True,
        blank=True,
    )
    status = models.CharField(
        max_length=50,
        choices=Status.choices,
        verbose_name=_("Status"),
        default=Status.DRAFTED.value,
    )
    name = models.CharField(max_length=255, verbose_name=_("Name"))
    logo = models.OneToOneField(
        OrganizationLogoFile,
        on_delete=models.SET_NULL,
        verbose_name=_("Logo"),
        null=True,
        blank=True,
        related_name="organization",
    )
    short_name = models.CharField(max_length=255, verbose_name=_("Short Name"), null=True, blank=True)
    national_number = models.CharField(max_length=255, verbose_name=_("National Number"), null=True, blank=True)
    type = models.CharField(max_length=50, choices=Type.choices, verbose_name=_("Type"), null=True, blank=True)
    business_type = models.CharField(
        max_length=50,
        choices=BussinessType.choices,
        verbose_name=_("Business Type"),
        null=True,
        blank=True,
    )
    industry = models.ForeignKey(
        Industry,
        on_delete=models.SET_NULL,
        verbose_name=_("Industry"),
        null=True,
        blank=True,
        related_name="organizations",
    )
    roles = GenericRelation(
        Role,
        verbose_name=_("Roles"),
        related_query_name="organization",
        content_type_field=Role.managed_by_model.field.name,
        object_id_field=Role.managed_by_id.field.name,
    )
    established_at = models.DateField(verbose_name=_("Established At"), null=True, blank=True)
    city = models.ForeignKey(
        City, on_delete=models.SET_NULL, verbose_name=_("City"), null=True, blank=True, related_name="organizations"
    )
    size = models.CharField(max_length=50, choices=Size.choices, verbose_name=_("Size"), null=True, blank=True)
    about = models.TextField(verbose_name=_("About"), null=True, blank=True)
    allow_self_verification = None
    employees = models.ManyToManyField(User, through="OrganizationEmployee", related_name="employee_organizations")

    class Meta:
        verbose_name = _("Organization")
        verbose_name_plural = _("Organizations")

    def __init__(self, *args, **kwargs):
        self._meta.get_field(Organization.user.field.name).verbose_name = _("Owner")
        super().__init__(*args, **kwargs)

    def __str__(self):
        return self.name

    @classmethod
    def get_verification_abstract_model(cls):
        return OrganizationVerificationMethodAbstract

    @classmethod
    def get_verified_statuses(cls):
        return [cls.Status.VERIFIED]

    def get_membership(self, user: User) -> Optional["OrganizationMembership"]:
        if not (accessor := getattr(self, OrganizationMembership.organization.related_query_name(), None)):
            return

        return accessor.filter(**{OrganizationMembership.user.field.name: user}).first()


class OrganizationVerificationMethodAbstract(DocumentVerificationMethodAbstract):
    organization = models.OneToOneField(Organization, on_delete=models.CASCADE, verbose_name=_("Organization"))
    DOCUMENT_FIELD = "organization"

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.organization} Verification"

    def get_output(self):
        pass

    def _update_status(self, status: Organization.Status):
        self.organization.status = status
        self.organization.save(update_fields=["status"])

    def verify(self) -> bool:
        self.verified_at = now()
        self.save(update_fields=["verified_at"])
        self._update_status(Organization.Status.VERIFIED)
        return True

    def reject(self):
        self._update_status(Organization.Status.REJECTED)


class DNSTXTRecordMethod(OrganizationVerificationMethodAbstract):
    code = models.CharField(
        max_length=20,
        verbose_name=_("code"),
        default=generate_dnc_txt_record_code,
        unique=True,
    )

    class Meta:
        verbose_name = _("DNS TXT Record Method")
        verbose_name_plural = _("DNS TXT Record Methods")

    def get_output(self):
        return {"code": self.code}


class UploadFileToWebsiteMethod(OrganizationVerificationMethodAbstract):
    file_name = models.CharField(
        max_length=30, verbose_name=_("File Name"), default=generate_unique_file_name, unique=True
    )

    class Meta:
        verbose_name = _("Upload File To Website Method")
        verbose_name_plural = _("Upload File To Website Methods")

    def get_output(self):
        return {"file_name": self.file_name}


class OrganizationCertificateFile(UserUploadedDocumentFile):
    SLUG = FileSlugs.ORGANIZATION_CERTIFICATE.value

    def get_upload_path(self, filename):
        return f"organization/certificate/{self.uploaded_by.id}/{filename}"

    def check_auth(self, request):
        return request.user == self.uploaded_by

    class Meta:
        verbose_name = _("Organization Certificate File")
        verbose_name_plural = _("Organization Certificate Files")


class UploadCompanyCertificateMethod(OrganizationVerificationMethodAbstract):
    organization_certificate_file = models.OneToOneField(
        OrganizationCertificateFile,
        on_delete=models.CASCADE,
        related_name="upload_company_certificate_method",
        verbose_name=_("Organization Certificate"),
    )

    class Meta:
        verbose_name = _("Upload Company Certificate Method")
        verbose_name_plural = _("Upload Company Certificate Methods")


class CommunicateOrganizationMethod(OrganizationVerificationMethodAbstract):
    phonenumber = PhoneNumberField(verbose_name=_("Phone Number"))
    email = models.EmailField(verbose_name=_("Email"), null=True, blank=True)
    is_phonenumber_verified = models.BooleanField(default=False, verbose_name=_("Is Phone Number Verified"))

    class Meta:
        verbose_name = _("Communicate Organization Method")
        verbose_name_plural = _("Communicate Organization Methods")

    def get_otp_cache_key(self) -> str:
        return ORGANIZATION_PHONE_OTP_CACHE_KEY % {"organization_id": self.organization.pk}

    def get_otp(self) -> Optional[str]:
        return cache.get(self.get_otp_cache_key())

    get_otp.short_description = _("OTP")

    def generate_otp(self) -> str:
        cache.set(self.get_otp_cache_key(), (otp := get_phone_otp()), timeout=ORGANIZATION_PHONE_OTP_EXPIRY)
        return otp

    def get_or_create_otp(self) -> str:
        if otp := self.get_otp():
            return otp
        otp = self.generate_otp()
        return otp

    def send_otp_sms(self, request):
        from notification.models import SMSNotification
        from notification.senders import NotificationContext, send_notifications

        send_notifications(
            NotificationContext(
                notification=SMSNotification(
                    user=request.user,
                    phone_number=self.phonenumber,
                    body=render_to_string(
                        "sms/organization_sms_verification.html",
                        {"otp": self.get_or_create_otp(), "organization": self.organization},
                    ),
                )
            )
        )

    def verify_otp(self, input_otp: str) -> bool:
        if (otp := self.get_otp()) and otp == input_otp:
            cache.delete(self.get_otp_cache_key())
            self.is_phonenumber_verified = True
            self.save(update_fields=[CommunicateOrganizationMethod.is_phonenumber_verified.field.name])
            return True
        return False

    @property
    def is_verified(self):
        return self.is_phonenumber_verified

    def after_create(self, request):
        self.send_otp_sms(request)


class OrganizationMembership(models.Model):
    role = models.ForeignKey(
        Role,
        on_delete=models.RESTRICT,
        related_name="organization_memberships",
        verbose_name=_("Access Role"),
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="memberships",
        verbose_name=_("Organization"),
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="organization_memberships",
        verbose_name=_("User"),
    )
    invited_by = models.ForeignKey(
        User,
        verbose_name=_("Invited By"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="invited_memberships",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))

    @classmethod
    def flex_report_search_fields(cls):
        return [
            fj(cls.user, User.email),
            fj(
                cls.user,
                Profile.user.field.related_query_name(),
                Profile.gender,
            ),
        ]

    class Meta:
        verbose_name = _("Organization Membership")
        verbose_name_plural = _("Organization Memberships")

    def __str__(self):
        return f"{self.user.email} - {self.organization.name}"


class OrganizationInvitation(models.Model):
    email = models.EmailField(verbose_name=_("Email"))
    organization = models.ForeignKey(
        "Organization",
        on_delete=models.CASCADE,
        verbose_name=_("Organization"),
        related_name="invitations",
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.RESTRICT,
        related_name="organization_invitations",
        verbose_name=_("Role"),
    )
    token = models.CharField(
        max_length=15,
        verbose_name=_("Token"),
        unique=True,
        db_index=True,
        default=generate_invitation_token,
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_("Created By"))

    objects = OrganizationInvitationManager()

    class Meta:
        verbose_name = _("Organization Invitation")
        verbose_name_plural = _("Organization Invitations")

    def __str__(self):
        return f"{self.email} - {self.organization.name}"


class OrganizationJobPosition(ChangeStateMixin, models.Model):
    class Status(models.TextChoices):
        DRAFTED = "drafted", _("Drafted")
        PUBLISHED = "published", _("Published")
        COMPLETED = "completed", _("Completed")
        SUSPENDED = "suspended", _("Suspended")
        EXPIRED = "expired", _("Expired")

    class PaymentTerm(models.TextChoices):
        HOURLY = "hourly", _("Hourly")
        DAILY = "daily", _("Daily")
        WEEKLY = "weekly", _("Weekly")
        MONTHLY = "monthly", _("Monthly")
        YEARLY = "yearly", _("Yearly")

    class WeekDay(models.TextChoices):
        MONDAY = "monday", _("Monday")
        TUESDAY = "tuesday", _("Tuesday")
        WEDNESDAY = "wednesday", _("Wednesday")
        THURSDAY = "thursday", _("Thursday")
        FRIDAY = "friday", _("Friday")
        SATURDAY = "saturday", _("Saturday")
        SUNDAY = "sunday", _("Sunday")

    title = models.CharField(max_length=255, verbose_name=_("Title"), null=True, blank=True)
    vaccancy = models.PositiveIntegerField(verbose_name=_("Vacancy"), null=True, blank=True)
    start_at = models.DateField(verbose_name=_("Start At"), null=True, blank=True)
    validity_date = models.DateField(verbose_name=_("Validity Date"), null=True, blank=True)
    description = MarkdownField(
        rendered_field="description_rendered", validator=VALIDATOR_STANDARD, null=True, blank=True
    )
    skills = models.ManyToManyField(Skill, verbose_name=_("Skills"), related_name="job_positions", blank=True)
    fields = models.ManyToManyField(Field, verbose_name=_("Fields"), related_name="job_positions", blank=True)
    degrees = ArrayField(
        models.CharField(choices=Education.Degree.choices, max_length=50),
        verbose_name=_("Degrees"),
        null=True,
        blank=True,
    )
    work_experience_years_range = IntegerRangeField(verbose_name=_("Age Range"), null=True, blank=True)
    languages = ArrayField(
        models.CharField(choices=LANGUAGES, max_length=32),
        verbose_name=_("Languages"),
        null=True,
        blank=True,
    )
    native_languages = ArrayField(
        models.CharField(choices=LANGUAGES, max_length=32),
        verbose_name=_("Native Languages"),
        null=True,
        blank=True,
    )
    age_range = IntegerRangeField(verbose_name=_("Age Range"), null=True, blank=True)
    required_documents = ArrayField(
        models.CharField(max_length=255), verbose_name=_("Required Document"), null=True, blank=True
    )
    performance_expectation = MarkdownField(
        rendered_field="performance_expectation_rendered", validator=VALIDATOR_STANDARD, null=True, blank=True
    )
    contract_type = models.CharField(
        max_length=50,
        choices=Profile.JobType.choices,
        verbose_name=_("Contract Type"),
        null=True,
        blank=True,
    )
    location_type = models.CharField(
        max_length=50, choices=Profile.JobLocationType.choices, verbose_name=_("Location Type"), null=True, blank=True
    )
    salary_range = IntegerRangeField(verbose_name=_("Salary Range"), null=True, blank=True)
    payment_term = models.CharField(
        max_length=50,
        choices=PaymentTerm.choices,
        verbose_name=_("Payment Term"),
        null=True,
        blank=True,
    )
    working_start_at = models.TimeField(verbose_name=_("Working Start At"), null=True, blank=True)
    working_end_at = models.TimeField(verbose_name=_("Working End At"), null=True, blank=True)
    benefits = models.ManyToManyField(JobBenefit, verbose_name=_("Benefits"), related_name="job_positions", blank=True)
    other_benefits = ArrayField(
        models.CharField(max_length=255), verbose_name=_("Other Benefits"), null=True, blank=True
    )
    days_off = ArrayField(
        models.CharField(choices=WeekDay.choices, max_length=50),
        verbose_name=_("Days Off"),
        null=True,
        blank=True,
    )
    job_restrictions = models.TextField(verbose_name=_("Job Restrictions"), null=True, blank=True)
    employer_questions = ArrayField(
        models.CharField(max_length=255),
        verbose_name=_("Employer Questions"),
        null=True,
        blank=True,
    )
    city = models.ForeignKey(
        City, on_delete=models.SET_NULL, verbose_name=_("City"), related_name="job_positions", null=True, blank=True
    )

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="job_positions")
    job_seeker_assignment = models.ManyToManyField(
        User, through="JobPositionAssignment", verbose_name=_("Job Seeker Assignment")
    )
    status = models.CharField(
        max_length=50,
        choices=Status.choices,
        verbose_name=_("Status"),
        default=Status.DRAFTED.value,
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))

    class Meta:
        verbose_name = _("Organization Job Position")
        verbose_name_plural = _("Organization Job Positions")

    def __str__(self):
        return f"{self.title} - {self.organization.name}"

    @classmethod
    def set_expiry(cls):
        expired_job_positions = cls.objects.filter(
            **{fj(cls.validity_date, LessThan.lookup_name): now().date()}
        ).exclude(**{fj(cls.status): cls.Status.EXPIRED})
        expired_job_positions.update(**{fj(cls.status): cls.Status.EXPIRED})
        for job_position in expired_job_positions:
            job_position.set_status_history()

    @property
    def is_editable(self):
        return self.status == OrganizationJobPosition.Status.DRAFTED.value and not self.assignments.count()

    def set_status_history(self):
        OrganizationJobPositionStatusHistory.objects.create(job_position=self, status=self.status)

    def clean(self):
        if self.start_at and self.validity_date and self.start_at > self.validity_date:
            raise ValidationError({"validity_date": _("Validity date must be after Start date")})

        if self.working_start_at and self.working_end_at and self.working_start_at > self.working_end_at:
            raise ValidationError({"working_end_at": _("Working End At must be after Working Start At")})
        return super().clean()

    @property
    def required_fields(self):
        return [
            OrganizationJobPosition.title.field.name,
        ]

    def change_status(self, new_status, *args, **kwargs):
        super().change_status(
            new_status,
            {
                self.Status.DRAFTED: DraftedState(),
                self.Status.PUBLISHED: PublishedState(),
                self.Status.COMPLETED: CompletedState(),
                self.Status.SUSPENDED: SuspendedState(),
                self.Status.EXPIRED: ExpiredState(),
            },
            OrganizationJobPosition.status.field.name,
            **kwargs,
        )


class DraftedState(GenericState):
    new_statuses = [
        OrganizationJobPosition.Status.PUBLISHED.value,
    ]

    @classmethod
    def change_status(cls, job_position, new_status, status_field, **kwargs):
        super().change_status(job_position, new_status, status_field, **kwargs)
        missing_fields = [field for field in job_position.required_fields if not getattr(job_position, field)]
        if missing_fields:
            raise GraphQLErrorBadRequest(f"Missing required fields for publishing: {', '.join(missing_fields)}")

        if job_position.organization.status not in Organization.get_verified_statuses():
            raise GraphQLErrorBadRequest(("Organization must be verified to publish job positions"))


class PublishedState(GenericState):
    new_statuses = [
        OrganizationJobPosition.Status.DRAFTED.value,
        OrganizationJobPosition.Status.SUSPENDED.value,
    ]


class CompletedState(GenericState):
    new_statuses = [
        OrganizationJobPosition.Status.DRAFTED.value,
    ]


class SuspendedState(GenericState):
    new_statuses = [
        OrganizationJobPosition.Status.DRAFTED.value,
        OrganizationJobPosition.Status.PUBLISHED.value,
    ]


class ExpiredState(GenericState):
    new_statuses = [
        OrganizationJobPosition.Status.DRAFTED.value,
    ]


class OrganizationJobPositionStatusHistory(models.Model):
    job_position = models.ForeignKey(OrganizationJobPosition, on_delete=models.CASCADE, related_name="status_histories")
    status = models.CharField(max_length=50, choices=OrganizationJobPosition.Status.choices, verbose_name=_("Status"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))

    class Meta:
        verbose_name = _("Organization Job Position Status History")
        verbose_name_plural = _("Organization Job Position Status Histories")

    def __str__(self):
        return f"{self.job_position.title} - {self.status}"


class JobPositionAssignment(ChangeStateMixin, models.Model):
    class Status(models.TextChoices):
        AWAITING_JOBSEEKER_APPROVAL = "awaiting_jobseeker_approval", _("Awaiting Jobseeker Approval")
        REJECTED_BY_JOBSEEKER = "rejected_by_jobseeker", _("Rejected By Jobseeker")
        NOT_REVIEWED = "not_reviewed", _("Not Reviewed")
        AWAITING_INTERVIEW_DATE = "awaiting_interview_date", _("Awaiting Interview Date")
        INTERVIEW_SCHEDULED = "interview_scheduled", _("Interview Scheduled")
        INTERVIEWING = "interviewing", _("Interviewing")
        AWAITING_INTERVIEW_RESULTS = "awaiting_interview_results", _("Awaiting Interview Results")
        INTERVIEW_CANCELED_BY_JOBSEEKER = "interview_canceled_by_jobseeker", _("Interview Canceled By Jobseeker")
        INTERVIEW_CANCELED_BY_EMPLOYER = "interview_canceled_by_employer", _("Interview Canceled By Employer")
        REJECTED_AT_INTERVIEW = "rejected_at_interview", _("Rejected At Interview")
        REJECTED = "rejected", _("Rejected")
        ACCEPTED = "accepted", _("Accepted")

    job_seeker = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name=_("Job Seeker"), related_name="job_position_assignments"
    )
    job_position = models.ForeignKey(
        OrganizationJobPosition, on_delete=models.CASCADE, verbose_name=_("Job Position"), related_name="assignments"
    )
    status = models.CharField(
        max_length=50,
        choices=Status.choices,
        verbose_name=_("Status"),
        default=Status.AWAITING_JOBSEEKER_APPROVAL.value,
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))

    class Meta:
        verbose_name = _("Job Position Assignment")
        verbose_name_plural = _("Job Position Assignments")
        unique_together = [("job_seeker", "job_position")]

    def __str__(self):
        return f"{self.job_position.title} - {self.job_seeker.email}"

    @property
    def organization_related_statuses(self):
        return [
            self.Status.NOT_REVIEWED,
            self.Status.AWAITING_INTERVIEW_DATE,
            self.Status.INTERVIEW_SCHEDULED,
            self.Status.INTERVIEWING,
            self.Status.AWAITING_INTERVIEW_RESULTS,
            self.Status.INTERVIEW_CANCELED_BY_EMPLOYER,
            self.Status.REJECTED_AT_INTERVIEW,
            self.Status.REJECTED,
            self.Status.ACCEPTED,
        ]

    @property
    def job_seeker_related_statuses(self):
        return [
            self.Status.AWAITING_JOBSEEKER_APPROVAL,
            self.Status.REJECTED_BY_JOBSEEKER,
        ]

    @staticmethod
    def get_job_seeker_specific_statuses():
        return [
            JobPositionAssignment.Status.AWAITING_JOBSEEKER_APPROVAL,
            JobPositionAssignment.Status.REJECTED_BY_JOBSEEKER,
        ]

    def set_status_history(self):
        return JobPositionAssignmentStatusHistory.objects.create(job_position_assignment=self, status=self.status)

    def change_status(self, new_status, **kwargs):
        super().change_status(
            new_status,
            {
                self.Status.AWAITING_JOBSEEKER_APPROVAL: AwaitingJobseekerApprovalState(),
                self.Status.REJECTED_BY_JOBSEEKER: RejectedByJobseekerState(),
                self.Status.NOT_REVIEWED: NotReviewedState(),
                self.Status.AWAITING_INTERVIEW_DATE: AwaitingInterviewDateState(),
                self.Status.INTERVIEW_SCHEDULED: InterviewScheduledState(),
                self.Status.INTERVIEWING: InterviewingState(),
                self.Status.AWAITING_INTERVIEW_RESULTS: AwaitingInterviewResultsState(),
                self.Status.INTERVIEW_CANCELED_BY_JOBSEEKER: InterviewCanceledByJobseekerState(),
                self.Status.INTERVIEW_CANCELED_BY_EMPLOYER: InterviewCanceledByEmployerState(),
                self.Status.REJECTED_AT_INTERVIEW: RejectedAtInterviewState(),
                self.Status.REJECTED: RejectedState(),
                self.Status.ACCEPTED: AccptedState(),
            },
            JobPositionAssignment.status.field.name,
            **kwargs,
        )


class JobPositionAssignmentStatusHistory(models.Model):
    job_position_assignment = models.ForeignKey(
        JobPositionAssignment, on_delete=models.CASCADE, related_name="status_histories"
    )
    status = models.CharField(
        max_length=50,
        choices=JobPositionAssignment.Status.choices,
        verbose_name=_("Status"),
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))

    class Meta:
        verbose_name = _("Job Position Assignment Status History")
        verbose_name_plural = _("Job Position Assignment Status Histories")

    def __str__(self):
        return f"{self.job_position_assignment}: {self.status}"


class JobPositionInterview(models.Model):
    job_position_assignment = models.ForeignKey(
        JobPositionAssignment,
        on_delete=models.CASCADE,
        verbose_name=_("Job Position Assignment"),
        related_name="interviews",
    )
    assignment_status_history = models.OneToOneField(
        JobPositionAssignmentStatusHistory, on_delete=models.RESTRICT, related_name="interview", null=True, blank=True
    )
    interview_date = models.DateTimeField(verbose_name=_("Interview Date"))
    result_date = models.DateTimeField(verbose_name=_("Result Date"), null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))

    class Meta:
        verbose_name = _("Job Position Interview")
        verbose_name_plural = _("Job Position Interviews")

    def __str__(self):
        return f"{self.job_position_assignment} - Interview date: {self.interview_date}"


class AwaitingJobseekerApprovalState(GenericState):
    new_statuses = [
        JobPositionAssignment.Status.REJECTED_BY_JOBSEEKER.value,
        JobPositionAssignment.Status.NOT_REVIEWED.value,
    ]


class RejectedByJobseekerState(GenericState):
    new_statuses = []


class NotReviewedState(GenericState):
    new_statuses = [
        JobPositionAssignment.Status.AWAITING_INTERVIEW_DATE.value,
        JobPositionAssignment.Status.REJECTED.value,
    ]


class AwaitingInterviewDateState(GenericState):
    new_statuses = [
        JobPositionAssignment.Status.INTERVIEW_SCHEDULED.value,
        JobPositionAssignment.Status.INTERVIEW_CANCELED_BY_EMPLOYER.value,
        JobPositionAssignment.Status.INTERVIEW_CANCELED_BY_JOBSEEKER.value,
    ]

    @classmethod
    def change_status(cls, job_position_assignment, new_status, status_field, **kwargs):
        assignment_status_history = super().change_status(job_position_assignment, new_status, status_field, **kwargs)
        if new_status.value == JobPositionAssignment.Status.INTERVIEW_SCHEDULED.value:
            if interview_date := kwargs.get("interview_date"):
                JobPositionInterview.objects.create(
                    job_position_assignment=job_position_assignment,
                    interview_date=interview_date,
                    assignment_status_history=assignment_status_history,
                )
            else:
                raise ValueError(_("Interview date is required"))


class InterviewScheduledState(GenericState):
    new_statuses = [
        JobPositionAssignment.Status.INTERVIEWING.value,
        JobPositionAssignment.Status.INTERVIEW_CANCELED_BY_EMPLOYER.value,
        JobPositionAssignment.Status.INTERVIEW_CANCELED_BY_JOBSEEKER.value,
    ]


class InterviewingState(GenericState):
    new_statuses = [
        JobPositionAssignment.Status.AWAITING_INTERVIEW_RESULTS.value,
    ]

    @classmethod
    def change_status(cls, job_position_assignment, new_status, status_field, **kwargs):
        super().change_status(job_position_assignment, new_status, status_field, **kwargs)
        if result_date := kwargs.get("result_date"):
            job_position_interview = job_position_assignment.interviews.last()
            job_position_interview.result_date = result_date
            job_position_interview.save(update_fields=["result_date"])
        else:
            raise ValueError(_("Result date is required"))


class AwaitingInterviewResultsState(GenericState):
    new_statuses = [
        JobPositionAssignment.Status.REJECTED_AT_INTERVIEW.value,
        JobPositionAssignment.Status.ACCEPTED.value,
    ]

    @classmethod
    def change_status(cls, job_position_assignment, new_status, status_field, **kwargs):
        super().change_status(job_position_assignment, new_status, status_field, **kwargs)
        if new_status.value == JobPositionAssignment.Status.ACCEPTED.value:
            organization_employee, _ = OrganizationEmployee.objects.get_or_create(
                user=job_position_assignment.job_seeker, organization=job_position_assignment.job_position.organization
            )
            OrganizationEmployeeCooperation.objects.create(
                employee=organization_employee,
                job_position_assignment=job_position_assignment,
            )


class InterviewCanceledByJobseekerState(GenericState):
    new_statuses = [
        JobPositionAssignment.Status.REJECTED.value,
        JobPositionAssignment.Status.AWAITING_INTERVIEW_DATE.value,
    ]


class InterviewCanceledByEmployerState(GenericState):
    new_statuses = [
        JobPositionAssignment.Status.REJECTED.value,
        JobPositionAssignment.Status.AWAITING_INTERVIEW_DATE.value,
    ]


class RejectedAtInterviewState(GenericState):
    new_statuses = []


class RejectedState(GenericState):
    new_statuses = []


class AccptedState(GenericState):
    new_statuses = []


class OrganizationEmployee(TimeStampedModel):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=_("User"),
        related_name="organization_employees",
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        verbose_name=_("Organization"),
        related_name="organization_employees",
    )

    class Meta:
        verbose_name = _("Organization Employee")
        verbose_name_plural = _("Organization Employees")
        unique_together = [("user", "organization")]

    def __str__(self):
        return f"{self.user.email} - {self.organization.name}"


class OrganizationEmployeeCooperation(ChangeStateMixin, models.Model):
    class Status(models.TextChoices):
        AWAITING = "awaiting", _("Awaiting")
        ACTIVE = "active", _("Active")
        SUSPENDED = "suspended", _("Suspended")
        FIRED = "fired", _("Fired")
        RESIGNED = "resigned", _("Resigned")
        FINISHED = "finished", _("Finished")

    status = models.CharField(
        max_length=50,
        choices=Status.choices,
        verbose_name=_("Status"),
        default=Status.AWAITING,
    )
    employee = models.ForeignKey(
        OrganizationEmployee,
        on_delete=models.CASCADE,
        verbose_name=_("Organization Employee"),
        related_name="cooperations",
    )
    job_position_assignment = models.ForeignKey(
        JobPositionAssignment,
        on_delete=models.RESTRICT,
        verbose_name=_("Job Position Assignment"),
        related_name="cooperations",
    )
    start_at = models.DateTimeField(verbose_name=_("Start At"), null=True, blank=True)
    end_at = models.DateTimeField(verbose_name=_("End At"), null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))

    class Meta:
        verbose_name = _("Organization Employee Cooperation")
        verbose_name_plural = _("Organization Employee Cooperation")

    def clean(self):
        if self.job_position_assignment.job_seeker != self.employee.user:
            raise ValidationError(
                _("Job Position Assignment's job seeker must be the same as Organization Employee's user.")
            )

        # TODO: test below before commit
        if (
            OrganizationEmployeeCooperation.objects.filter(
                **{
                    fj(OrganizationEmployeeCooperation.employee, OrganizationEmployee.user): self.employee.user,
                    fj(OrganizationEmployeeCooperation.status, In.lookup_name): [
                        self.Status.AWAITING,
                        self.Status.ACTIVE,
                        self.Status.SUSPENDED,
                    ],
                }
            )
            .exclude(
                **{fj(OrganizationEmployeeCooperation.employee): self.employee},
            )
            .exists()
        ):
            raise ValidationError(_("Employee already has an active cooperation."))

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.id}: {self.employee} - {self.start_at or ''} - {self.end_at or ''}"

    def set_status_history(self):
        OrganizationEmployeeCooperationStatusHistory.objects.create(
            organization_employee_cooperation=self, status=self.status
        )

    def change_status(self, new_status, **kwargs):
        super().change_status(
            new_status,
            {
                self.Status.AWAITING: HiringAwaitingState(),
                self.Status.ACTIVE: HiringActiveState(),
                self.Status.SUSPENDED: HiringSuspendedState(),
                self.Status.FINISHED: HiringFinishedState(),
                self.Status.FIRED: HiringFiredState(),
                self.Status.RESIGNED: HiringResignedState(),
            },
            OrganizationEmployeeCooperation.status.field.name,
            **kwargs,
        )

    @classmethod
    def check(cls, **kwargs):
        errors = super().check(**kwargs)
        if set(cls.get_status_order()) != {status.value for status in cls.Status}:
            errors.append(checks.Error("Mismatch in get_status_order().", obj=cls))
        return errors

    @classmethod
    def get_status_order(cls):
        return [
            cls.Status.AWAITING,
            cls.Status.ACTIVE,
            cls.Status.SUSPENDED,
            cls.Status.FINISHED,
            cls.Status.FIRED,
            cls.Status.RESIGNED,
        ]

    @property
    def organization_related_statuses(self):
        return [
            self.Status.AWAITING,
            self.Status.ACTIVE,
            self.Status.SUSPENDED,
            self.Status.FINISHED,
            self.Status.FIRED,
        ]

    @property
    def job_seeker_related_statuses(self):
        return [
            self.Status.RESIGNED,
        ]


class HiringAwaitingState(GenericState):
    new_statuses = [
        OrganizationEmployeeCooperation.Status.ACTIVE.value,
    ]

    @classmethod
    def change_status(cls, organization_employee_cooperation, new_status, status_field, **kwargs):
        organization_employee_cooperation.start_at = now()
        organization_employee_cooperation.save(update_fields=[OrganizationEmployeeCooperation.start_at.field.name])
        super().change_status(organization_employee_cooperation, new_status, status_field, **kwargs)


class HiringActiveState(GenericState):
    new_statuses = [
        OrganizationEmployeeCooperation.Status.SUSPENDED.value,
        OrganizationEmployeeCooperation.Status.FIRED.value,
        OrganizationEmployeeCooperation.Status.RESIGNED.value,
        OrganizationEmployeeCooperation.Status.FINISHED.value,
    ]

    @classmethod
    def change_status(cls, organization_employee_cooperation, new_status, status_field, **kwargs):
        super().change_status(organization_employee_cooperation, new_status, status_field, **kwargs)
        if new_status.value in [
            OrganizationEmployeeCooperation.Status.FIRED.value,
            OrganizationEmployeeCooperation.Status.RESIGNED.value,
            OrganizationEmployeeCooperation.Status.FINISHED.value,
        ]:
            organization_employee_cooperation.end_at = now()
            organization_employee_cooperation.save(update_fields=[OrganizationEmployeeCooperation.end_at.field.name])


class HiringSuspendedState(GenericState):
    new_statuses = [
        OrganizationEmployeeCooperation.Status.ACTIVE.value,
        OrganizationEmployeeCooperation.Status.RESIGNED.value,
    ]


class HiringFinishedState(GenericState):
    new_statuses = []


class HiringFiredState(GenericState):
    new_statuses = []


class HiringResignedState(GenericState):
    new_statuses = []


class OrganizationEmployeeCooperationStatusHistory(models.Model):
    organization_employee_cooperation = models.ForeignKey(
        OrganizationEmployeeCooperation,
        on_delete=models.CASCADE,
        verbose_name=_("Organization Employee Cooperation"),
        related_name="status_histories",
    )
    status = models.CharField(
        max_length=50,
        choices=OrganizationEmployeeCooperation.Status.choices,
        verbose_name=_("Status"),
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))

    class Meta:
        verbose_name = _("Organization Employee Cooperation Status History")
        verbose_name_plural = _("Organization Employee Cooperation Status Histories")

    def __str__(self):
        return f"{self.organization_employee_cooperation} - {self.status}"


class OrganizationPlatformMessage(TimeStampedModel):
    class Source(models.TextChoices):
        AI = "ai", _("AI")
        HUMAN = "human", _("Human")

    assignee_type = models.CharField(
        max_length=50,
        choices=User.RegistrationType.choices,
        verbose_name=_("Assignee"),
        default=User.RegistrationType.ORGANIZATION.value,
    )
    source = models.CharField(
        max_length=8,
        choices=Source.choices,
        verbose_name=_("Source"),
        default=Source.HUMAN.value,
    )
    title = models.CharField(max_length=255, verbose_name=_("Title"))
    text = models.TextField(verbose_name=_("Text"))
    organization_employee_cooperation = models.ForeignKey(
        OrganizationEmployeeCooperation,
        on_delete=models.CASCADE,
        verbose_name=_("Employee Cooperation"),
        related_name="%(class)s",
    )
    read_at = models.DateTimeField(verbose_name=_("Read At"), null=True, blank=True)

    class Meta:
        verbose_name = _("Organization Platform Message")
        verbose_name_plural = _("Organization Platform Messages")

    def __str__(self):
        return f"{self.title} - {self.organization_employee_cooperation}"


class OrganizationPlatformMessageAttachment(models.Model):
    organization_platform_message = models.ForeignKey(
        OrganizationPlatformMessage,
        on_delete=models.CASCADE,
        verbose_name=_("Organization Platform Message"),
        related_name="links",
    )
    text = models.CharField(max_length=255, verbose_name=_("Text"))
    url = models.URLField(verbose_name=_("URL"))

    class Meta:
        verbose_name = _("Organization Platform Message Link")
        verbose_name_plural = _("Organization Platform Message Links")

    def __str__(self):
        return f"{self.organization_platform_message} - {self.text}"


class OrganizationEmployeePerformanceReport(TimeStampedModel):
    class Status(models.TextChoices):
        CREATED = "created", _("Created")
        COMPLETED_BY_ORGANIZATION = "completed_by_organization", _("Completed By Organization")
        COMPLETED_BY_JOB_SEEKER = "completed_by_job_seeker", _("Completed By Job Seeker")
        COMPLETED = "completed", _("Completed")

    status = models.CharField(max_length=50, choices=Status.choices, verbose_name=_("Status"), default=Status.CREATED)
    organization_employee_cooperation = models.ForeignKey(
        OrganizationEmployeeCooperation,
        on_delete=models.CASCADE,
        verbose_name=_("Employee Cooperation"),
        related_name="%(class)s",
    )
    title = models.CharField(max_length=255, verbose_name=_("Title"), null=True, blank=True)
    report_summary = models.TextField(verbose_name=_("Summary"), null=True, blank=True)
    report_text = models.TextField(verbose_name=_("Text"))
    date = models.DateField(verbose_name=_("Date"), null=True, blank=True)

    class Meta:
        verbose_name = _("Organization Employee Performance Report")
        verbose_name_plural = _("Organization Employee Performance Reports")

    def __str__(self):
        return f"{self.organization_employee_cooperation} - {self.title}"


class PerformanceReportQuestion(EavAttribute):
    class QuestionType(models.TextChoices):
        TRUE_FALSE = "true_false", _("True/False")
        MULTIPLE_CHOICE = "multiple_choice", _("Multiple Choice")
        OPEN_ENDED = "open_ended", _("Open Ended")

    title = models.CharField(max_length=255, verbose_name=_("Title"))
    type = models.CharField(max_length=20, choices=QuestionType.choices, verbose_name=_("Type"))
    weight = models.PositiveIntegerField(verbose_name=_("Weight"), default=1)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = _("Performance Report Question")
        verbose_name_plural = _("Performance Report Questions")


class PerformanceReportAnswer(EavValue):
    attribute_field_name = "question"
    organization_employee_performance_report = models.ForeignKey(
        OrganizationEmployeePerformanceReport,
        on_delete=models.CASCADE,
        verbose_name=_("Organization Employee Performance Report"),
        related_name="answers",
    )
    question = models.ForeignKey(PerformanceReportQuestion, on_delete=models.CASCADE, related_name="answers")
    respondent = models.CharField(
        max_length=20,
        choices=User.RegistrationType.choices,
        verbose_name=_("Respondent"),
    )

    def __str__(self):
        return f"{self.question} - {self.value}"

    class Meta:
        verbose_name = _("Performance Report Answer")
        verbose_name_plural = _("Performance Report Answers")

    def clean(self):
        try:
            super().clean()
        except ValidationError as e:
            message = ""

            if error := getattr(e, "error_dict", None):
                message = list(map(field_serializer(self.question.title), map(attrgetter("message"), error.values())))
            elif error := getattr(e, "error_list", None):
                message = list(map(field_serializer(self.question.title), map(attrgetter("message"), error)))

            raise ValidationError({PerformanceReportAnswer.value.field.name: message})


class OrganizationEmployeePerformanceReportStatusHistory(models.Model):
    organization_employee_performance_report = models.ForeignKey(
        OrganizationEmployeePerformanceReport,
        on_delete=models.CASCADE,
        verbose_name=_("Organization Employee Performance Report"),
        related_name="status_histories",
    )
    status = models.CharField(
        max_length=50,
        choices=OrganizationEmployeePerformanceReport.Status.choices,
        verbose_name=_("Status"),
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))

    class Meta:
        verbose_name = _("Organization Employee Performance Report Status History")
        verbose_name_plural = _("Organization Employee Performance Report Status Histories")

    def __str__(self):
        return f"{self.organization_employee_performance_report} - {self.status}"
