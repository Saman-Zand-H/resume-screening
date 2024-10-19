from datetime import date
from typing import Generic, Literal, Optional, TypeVar, Union

from pydantic import BaseModel, EmailStr, HttpUrl, RootModel
from pydantic_extra_types.phone_numbers import PhoneNumber

from ..choices import EducationDegree, IEEEvaluator, WorkExperienceGrade

DocumentT = TypeVar("DocumentT")
VerificationT = TypeVar("VerificationT")


class BaseAnalysisResponse(BaseModel, Generic[DocumentT, VerificationT]):
    is_valid: bool
    data: Optional[DocumentT] = None
    verification_method_data: Optional[VerificationT] = None


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
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class ReferenceCheckData(BaseModel):
    reference_name: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[PhoneNumber] = None
    position: Optional[str] = None


class PaystubsData(BaseModel):
    pass


WorkExperienceVerificationType = Union[ReferenceCheckData, PaystubsData]


class EducationData(BaseModel):
    degree: Optional[EducationDegreeType] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


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


AnalysisResponse = RootModel[Union[WorkExperienceAnalysisResponse, EducationAnalysisResponse]]
