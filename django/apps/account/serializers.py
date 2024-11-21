from datetime import date
from typing import List, Optional

from cities_light.models import City
from common.choices import LANGUAGES
from common.models import Field, Job, LanguageProficiencyTest, Skill, University
from common.utils import fields_join
from dj_rest_auth.registration.serializers import (
    SocialLoginSerializer as BaseSocialLoginSerializer,
)
from phonenumber_field.validators import validate_phonenumber
from pydantic import BaseModel, ValidationInfo, field_validator, model_validator

from django.core.validators import URLValidator
from django.db.models import Model
from django.db.models.lookups import In
from django.utils.translation import gettext_lazy as _

from .models import Contact, Education, Profile, User
from .validators import LinkedInUsernameValidator


class SocialLoginSerializer(BaseSocialLoginSerializer):
    is_new_user = False

    def get_social_login(self, *args, **kwargs):
        sociallogin = super().get_social_login(*args, **kwargs)
        self.is_new_user = not User.objects.filter(**{fields_join(User.email): sociallogin.user.email}).exists()
        return sociallogin


def get_existing_foreign_keys(model: Model, ids: List[int]) -> Optional[List[int]]:
    existing_ids = set(
        model.objects.filter(**{fields_join(model._meta.pk.attname, In.lookup_name): ids}).values_list(
            model._meta.pk.get_attname(),
            flat=True,
        )
    )
    return existing_ids or None


class ProfileModel(BaseModel):
    height: Optional[int] = None
    weight: Optional[int] = None
    skin_color: Optional[Profile.SkinColor] = None
    hair_color: Optional[str] = None
    eye_color: Optional[Profile.EyeColor] = None
    employment_status: Optional[Profile.EmploymentStatus] = None
    interested_jobs: Optional[List[int]] = None
    city_id: Optional[int] = None
    gender: Optional[Profile.Gender] = None
    birth_date: Optional[date] = None
    skills: Optional[List[int]] = None

    @field_validator("skills")
    def check_skills(cls, value):
        if value is not None:
            return get_existing_foreign_keys(Skill, value)

    @field_validator("interested_jobs")
    def check_interested_jobs(cls, value):
        if value is not None:
            return get_existing_foreign_keys(Job, value)

    @field_validator("city_id")
    def check_city_id(cls, value):
        if value is not None:
            return get_existing_foreign_keys(City, [value])


class ContactModel(BaseModel):
    type: Contact.Type
    value: str

    @field_validator("value")
    def validate_value(cls, value, info: ValidationInfo):
        contact_type = info.data.get("type")
        validators = {
            Contact.Type.PHONE: validate_phonenumber,
            Contact.Type.WEBSITE: URLValidator(),
            Contact.Type.LINKEDIN: LinkedInUsernameValidator(),
            Contact.Type.WHATSAPP: validate_phonenumber,
        }
        validator = validators.get(contact_type)
        if validator:
            validator(value)
        return value


class EducationModel(BaseModel):
    field_id: int
    degree: Education.Degree
    university_id: int
    start: date
    end: Optional[date] = None

    @field_validator("field_id")
    def check_field_id(cls, value):
        return get_existing_foreign_keys(Field, [value])

    @field_validator("university_id")
    def check_university_id(cls, value):
        return get_existing_foreign_keys(University, [value])

    @model_validator(mode="before")
    def validate_dates(cls, values):
        start = values.get("start")
        end = values.get("end")
        if start and end and start > end:
            raise ValueError(_("End date must be after the start date."))

        return values


class WorkExperienceModel(BaseModel):
    job_id: int
    start: date
    end: Optional[date] = None
    organization: str
    city_id: int

    @field_validator("job_id")
    def check_job_id(cls, value):
        return get_existing_foreign_keys(Job, [value])

    @field_validator("city_id")
    def check_city_id(cls, value):
        return get_existing_foreign_keys(City, [value])

    @model_validator(mode="before")
    def validate_dates(cls, values):
        start = values.get("start")
        end = values.get("end")
        if start and end and start > end:
            raise ValueError(_("End date must be after the start date."))

        return values


class LanguageCertificateModel(BaseModel):
    language: str
    test_id: int
    issued_at: date
    expired_at: date
    listening_score: float
    reading_score: float
    writing_score: float
    speaking_score: float
    band_score: float

    @field_validator("test_id")
    def check_test_id(cls, value):
        return get_existing_foreign_keys(LanguageProficiencyTest, [value])

    @model_validator(mode="before")
    def validate_scores_and_dates(cls, values):
        issued_at = values.get("issued_at")
        expired_at = values.get("expired_at")
        if issued_at and expired_at and issued_at > expired_at:
            raise ValueError(_("Expired date must be after the issued date."))

        return values

    @field_validator("language")
    def validate_language(cls, value):
        if not dict(LANGUAGES).get(value):
            raise ValueError(_("Language is not valid."))

        return value


class CertificateAndLicenseModel(BaseModel):
    title: str
    certifier: str
    issued_at: date
    expired_at: Optional[date] = None

    @model_validator(mode="before")
    def validate_dates(cls, values):
        issued_at = values.get("issued_at")
        expired_at = values.get("expired_at")
        if issued_at and expired_at and issued_at > expired_at:
            raise ValueError(_("Expired date must be after the issued date."))

        return values


class ResumeModel(BaseModel):
    profile: Optional[ProfileModel]
    contact: Optional[List[ContactModel]] = []
    education: Optional[List[EducationModel]] = []
    work_experience: Optional[List[WorkExperienceModel]] = []
    language_certificate: Optional[List[LanguageCertificateModel]] = []
    certificate_and_license: Optional[List[CertificateAndLicenseModel]] = []
