from typing import Dict, List, Literal, Optional, Union

from pydantic import BaseModel, RootModel

from ..choices import ContactType

CONTACT_TYPES = Literal[
    ContactType.WHATSAPP,
    ContactType.ADDRESS,
    ContactType.PHONE,
    ContactType.LINKEDIN,
    ContactType.WEBSITE,
]


class ContactInformation(BaseModel):
    type: CONTACT_TYPES
    value: str


class Education(BaseModel):
    title: Optional[str] = None
    duration: Optional[str] = None
    university_name: Optional[str] = None
    achievements: Optional[List[str]] = None


class WorkExperience(BaseModel):
    job: Optional[str] = None
    city: Optional[str] = None
    duration: Optional[str] = None
    achievements: Optional[List[str]] = None


CoreCompetencies = RootModel[Union[List[str], Dict[str, Union[str, int, List[str]]]]]


class ResumeJson(BaseModel):
    about_me: str
    headline: str
    educations: Optional[List[Education]] = []
    work_experiences: Optional[List[WorkExperience]] = []
    core_competencies: Optional[CoreCompetencies] = {}
    contact_informations: Optional[List[ContactInformation]] = []
