from datetime import date
from typing import Any, Dict, Generic, List, Literal, Optional, TypeVar, Union

from pydantic import BaseModel, EmailStr, HttpUrl, RootModel
from pydantic_extra_types.phone_numbers import PhoneNumber

from ..choices import EducationDegree, IEEEvaluator, WorkExperienceGrade
from ..constants import FileSlugs

DocumentT = TypeVar("DocumentT")
VerificationT = TypeVar("VerificationT")


class IsValid(BaseModel):
    is_valid: bool


class BaseAnalysisResponse(IsValid, Generic[DocumentT, VerificationT]):
    data: Optional[DocumentT] = None
    verification_method_data: Optional[VerificationT] = None


VERIFICATION_METHOD_NAMES = Literal[
    FileSlugs.EMPLOYER_LETTER,
    FileSlugs.PAYSTUBS,
    FileSlugs.EDUCATION_EVALUATION,
    FileSlugs.DEGREE,
    FileSlugs.LANGUAGE_CERTIFICATE,
    FileSlugs.CERTIFICATE,
]


WorkExperienceGradeType = Literal[
    WorkExperienceGrade.INTERN,
    WorkExperienceGrade.ASSOCIATE,
    WorkExperienceGrade.JUNIOR,
    WorkExperienceGrade.MID_LEVEL,
    WorkExperienceGrade.SENIOR,
    WorkExperienceGrade.MANAGER,
    WorkExperienceGrade.DIRECTOR,
    WorkExperienceGrade.CTO,
    WorkExperienceGrade.CFO,
    WorkExperienceGrade.CEO,
]

EducationDegreeType = Literal[
    EducationDegree.BACHELORS,
    EducationDegree.MASTERS,
    EducationDegree.PHD,
    EducationDegree.ASSOCIATE,
    EducationDegree.DIPLOMA,
    EducationDegree.CERTIFICATE,
]


IEEEvaluatorType = Literal[
    IEEEvaluator.WES,
    IEEEvaluator.IQAS,
    IEEEvaluator.ICAS,
    IEEEvaluator.CES,
    IEEEvaluator.OTHER,
]


class WorkExperienceData(BaseModel):
    job_title: Optional[str] = None
    job_grade: Optional[WorkExperienceGradeType] = None
    organization: Optional[str] = None
    start: Optional[str] = None
    end: Optional[str] = None


class ReferenceCheckData(BaseModel):
    reference_name: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[PhoneNumber] = None
    position: Optional[str] = None


class PaystubsData(BaseModel):
    pass


WorkExperienceVerificationType = Union[ReferenceCheckData, PaystubsData]


class CertificateAndLicenseData(BaseModel):
    title: Optional[str] = None
    certifier: Optional[str] = None
    issued_at: Optional[date] = None
    expired_at: Optional[date] = None


class LanguageCertificateData(BaseModel):
    issued_at: Optional[date] = None
    expired_at: Optional[date] = None
    language: Optional[str] = None
    test: Dict[str, Any] = {}
    values: List[Any]


class EducationData(BaseModel):
    degree: Optional[EducationDegreeType] = None
    start: Optional[str] = None
    end: Optional[str] = None


class IEEMethodData(BaseModel):
    evaluator: Optional[IEEEvaluatorType] = None


class CommunicationMethodData(BaseModel):
    university_email: Optional[EmailStr] = None
    website: Optional[HttpUrl] = None
    department: Optional[str] = None
    person: Optional[str] = None


EducationVerificationType = Union[IEEMethodData, CommunicationMethodData]


class WorkExperienceAnalysisResponse(BaseAnalysisResponse[WorkExperienceData, WorkExperienceVerificationType]):
    pass


class EducationAnalysisResponse(BaseAnalysisResponse[EducationData, EducationVerificationType]):
    pass


class CertificateAndLicenseAnalysisResponse(BaseAnalysisResponse[CertificateAndLicenseData, None]):
    pass


class LanguageCertificateAnalysisResponse(BaseAnalysisResponse[LanguageCertificateData, None]):
    pass


AnalysisResponse = RootModel[
    Union[
        WorkExperienceAnalysisResponse,
        EducationAnalysisResponse,
        CertificateAndLicenseAnalysisResponse,
        LanguageCertificateAnalysisResponse,
    ]
]


class OcrResponse(BaseModel):
    text_content: str
