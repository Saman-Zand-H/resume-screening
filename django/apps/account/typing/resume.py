from typing import Dict, List, Literal, Optional, Union

from pydantic import BaseModel, RootModel

from ..models import Contact

CONTACT_TYPES = Literal[
    Contact.Type.WHATSAPP,
    Contact.Type.ADDRESS,
    Contact.Type.PHONE,
    Contact.Type.LINKEDIN,
    Contact.Type.WEBSITE,
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
    educations: List[Education]
    work_experiences: List[WorkExperience]
    core_competencies: Optional[CoreCompetencies]
    contact_informations: List[ContactInformation]
