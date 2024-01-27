from pydantic import BaseModel, field_validator, ValidationInfo
from typing import List, Optional
from datetime import date
from enum import Enum

from django.core.validators import URLValidator
from phonenumber_field.validators import validate_phonenumber

from .validators import LinkedInUsernameValidator, WhatsAppValidator


class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    NOT_KNOWN = "not_known"
    NOT_APPLICABLE = "not_applicable"


class SkinColor(str, Enum):
    VERY_FAIR = "#FFDFC4"
    FAIR = "#F0D5B1"
    LIGHT = "#E5B897"
    LIGHT_MEDIUM = "#D9A377"
    MEDIUM = "#C68642"
    OLIVE = "#A86B33"
    BROWN = "#8D5524"
    DARK_BROWN = "#60391C"
    VERY_DARK = "#3B260B"
    DEEP = "#100C08"


class EyeColor(str, Enum):
    AMBER = "#FFBF00"
    BLUE = "#5DADEC"
    BROWN = "#6B4226"
    GRAY = "#BEBEBE"
    GREEN = "#1CAC78"
    HAZEL = "#8E7618"


class EmploymentStatus(str, Enum):
    EMPLOYED = "employed"
    UNEMPLOYED = "unemployed"


class ContactType(str, Enum):
    WEBSITE = "website"
    ADDRESS = "address"
    LINKEDIN = "linkedin"
    WHATSAPP = "whatsapp"
    PHONE = "phone"


class Degree(str, Enum):
    BACHELORS = "bachelors"
    MASTERS = "masters"
    PHD = "phd"
    ASSOCIATE = "associate"
    DIPLOMA = "diploma"
    CERTIFICATE = "certificate"


class DocumentStatus(str, Enum):
    DRAFTED = "drafted"
    SUBMITTED = "submitted"
    REJECTED = "rejected"
    VERIFIED = "verified"
    SELF_VERIFIED = "self_verified"


class UserModel(BaseModel):
    gender: Optional[Gender] = None
    birth_date: Optional[date] = None
    skills: Optional[List[int]] = None


class ProfileModel(BaseModel):
    user_id: int
    height: Optional[int] = None
    weight: Optional[int] = None
    skin_color: Optional[SkinColor] = None
    hair_color: Optional[str] = None
    eye_color: Optional[EyeColor] = None
    full_body_image: Optional[str] = None
    employment_status: Optional[EmploymentStatus] = None
    interested_jobs: Optional[List[int]] = None
    city_id: Optional[int] = None


class ContactModel(BaseModel):
    type: ContactType
    value: str

    @field_validator("value")
    def validate_value(cls, value, info: ValidationInfo):
        contact_type = info.data.get("type")
        validators = {
            ContactType.PHONE: validate_phonenumber,
            ContactType.WEBSITE: URLValidator(),
            ContactType.LINKEDIN: LinkedInUsernameValidator(),
            ContactType.WHATSAPP: WhatsAppValidator(),
        }
        validator = validators.get(contact_type)
        if validator:
            validator(value)
        return value


class EducationModel(BaseModel):
    user_id: int
    status: Optional[DocumentStatus] = None
    field_id: int
    degree: Degree
    university_id: int
    start: date
    end: Optional[date] = None


class WorkExperienceModel(BaseModel):
    user_id: int
    status: Optional[DocumentStatus] = None
    job_id: int
    start: date
    end: Optional[date] = None
    organization: str
    city_id: int


class LanguageCertificateModel(BaseModel):
    user_id: int
    status: Optional[DocumentStatus] = None
    language_id: int
    test_id: int
    issued_at: date
    expired_at: date
    listening_score: float
    reading_score: float
    writing_score: float
    speaking_score: float
    band_score: float


class CertificateAndLicenseModel(BaseModel):
    user_id: int
    status: Optional[DocumentStatus] = None
    title: str
    certifier: str
    issued_at: date
    expired_at: Optional[date] = None


class ResumeModel(BaseModel):
    user: Optional[UserModel]
    profile: Optional[ProfileModel]
    contact: Optional[List[ContactModel]] = []
    education: Optional[List[EducationModel]] = []
    work_experience: Optional[List[WorkExperienceModel]] = []
    language_certificate: Optional[List[LanguageCertificateModel]] = []
    certificate_and_license: Optional[List[CertificateAndLicenseModel]] = []
