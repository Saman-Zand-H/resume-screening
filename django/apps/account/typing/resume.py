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
    title: str
    duration: str
    university_name: str
    achievements: List[str]


class WorkExperience(BaseModel):
    job: str
    city: str
    duration: str
    achievements: List[str]


CoreCompetencies = RootModel[Union[List[str], Dict[str, Union[str, int, List[str]]]]]


class ResumeJson(BaseModel):
    about_me: str
    headline: str
    educations: Optional[List[Education]] = []
    work_experiences: Optional[List[WorkExperience]] = []
    core_competencies: Optional[CoreCompetencies] = {}
    contact_informations: Optional[List[ContactInformation]] = []
