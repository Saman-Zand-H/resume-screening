from typing import List, Optional

from pydantic import BaseModel, Field


class ContactInformation(BaseModel):
    first_name: str = Field(..., description="The full name of the individual.")
    last_name: str = Field(..., description="The full name of the individual.")
    professional_email_address: str = Field(..., description="The professional email address of the individual.")
    phone_number: str = Field(..., description="The phone number, including country code if applicable.")
    linkedin_profile_url: Optional[str] = Field(None, description="The LinkedIn profile URL of the individual.")
    city_and_province_or_territory: Optional[str] = Field(
        None, description="The city and province/territory where the individual resides."
    )


class WorkExperienceItem(BaseModel):
    job_title: str = Field(..., description="The title of the job held.")
    company_name: str = Field(..., description="The name of the company where the individual worked.")
    employment_dates: str = Field(..., description="The dates of employment.")
    achievements: Optional[List[str]] = Field(None, description="A list of achievements during employment.")


class EducationItem(BaseModel):
    degree: str = Field(..., description="The degree obtained.")
    institution: str = Field(..., description="The educational institution attended.")
    graduation_date: Optional[str] = Field(None, description="The date of graduation.")
    relevant_coursework_or_honors: Optional[List[str]] = Field(
        None, description="List of relevant coursework or honors received."
    )


class CertificationItem(BaseModel):
    certification_title: str = Field(..., description="The name of the certification or course.")
    certification_dates: Optional[str] = Field(None, description="The date of completion.")


class AdditionalInformationItem(BaseModel):
    section_title: str = Field(..., description="The title of the additional information section.")
    content: str = Field(..., description="The content of the additional information.")


class ResumeSchema(BaseModel):
    contact_information: Optional[ContactInformation] = Field(
        None, description="Contact information of the individual."
    )
    professional_summary: Optional[str] = Field(
        None, description="A brief 2-4 sentence summary about the individual's professional background."
    )
    core_competencies_or_skills: Optional[List[str]] = Field(
        None, description="Includes both technical and soft skills."
    )
    work_experience: Optional[List[WorkExperienceItem]] = Field(
        None, description="List of work experiences in reverse chronological order."
    )
    education: Optional[List[EducationItem]] = Field(
        None, description="List of educational qualifications starting with the highest degree."
    )
    certifications_and_professional_development: Optional[List[CertificationItem]] = Field(
        None, description="Additional certifications and professional courses/training."
    )
    additional_information: Optional[List[AdditionalInformationItem]] = Field(
        None, description="Any additional information that the individual wants to include."
    )
