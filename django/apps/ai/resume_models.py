from enum import Enum
from typing import List, Optional, Dict
from pydantic import BaseModel, Field


class DateFormat(Enum):
    """Standardized date formats."""
    MMYYYY = "MM/YYYY"
    YYYYMM = "YYYY-MM"
    PRESENT = "PRESENT"


class SkillCategory(Enum):
    """Categories for skills."""
    TECHNICAL = "TECHNICAL"
    SOFT = "SOFT"
    LANGUAGE = "LANGUAGE"
    DOMAIN = "DOMAIN"
    OTHER = "OTHER"


class ContactInfo(BaseModel):
    """Contact information from resume."""
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    links: Optional[List[str]] = None


class Education(BaseModel):
    """Education details from resume."""
    institution: str
    degree: str
    field_of_study: Optional[str] = None
    start_date: str  # Standardized to DateFormat
    end_date: str  # Standardized to DateFormat (could be PRESENT)
    gpa: Optional[float] = None
    achievements: Optional[List[str]] = None


class WorkExperience(BaseModel):
    """Work experience details from resume."""
    company: str
    position: str
    start_date: str  # Standardized to DateFormat
    end_date: str  # Standardized to DateFormat (could be PRESENT)
    responsibilities: List[str]
    achievements: Optional[List[str]] = None
    location: Optional[str] = None


class Skill(BaseModel):
    """Standardized skill with category and proficiency."""
    name: str  # Standardized skill name
    original_text: str  # Original text from resume
    category: SkillCategory
    proficiency: Optional[float] = None  # Scale of 0-1


class Project(BaseModel):
    """Project details from resume."""
    name: str
    description: Optional[str] = None
    start_date: Optional[str] = None  # Standardized to DateFormat
    end_date: Optional[str] = None  # Standardized to DateFormat
    technologies: Optional[List[str]] = None
    url: Optional[str] = None
    achievements: Optional[List[str]] = None


class Certification(BaseModel):
    """Certification details from resume."""
    name: str
    issuer: str
    date: Optional[str] = None  # Standardized to DateFormat
    expiry_date: Optional[str] = None  # Standardized to DateFormat
    url: Optional[str] = None


class Language(BaseModel):
    """Language proficiency."""
    name: str
    proficiency: str  # e.g., "Fluent", "Native", etc.


class ResumeAnalysisResult(BaseModel):
    """Complete resume analysis result."""
    contact_info: ContactInfo
    education: List[Education]
    work_experience: List[WorkExperience]
    skills: List[Skill]
    projects: Optional[List[Project]] = None
    certifications: Optional[List[Certification]] = None
    languages: Optional[List[Language]] = None
    
    # Analysis metrics
    extraction_confidence: Dict[str, float] = Field(
        default_factory=lambda: {
            "contact_info": 0.0,
            "education": 0.0,
            "work_experience": 0.0,
            "skills": 0.0,
            "projects": 0.0,
            "certifications": 0.0,
            "languages": 0.0,
        }
    )
    
    document_language: Optional[str] = None
    file_format: Optional[str] = None
    parsing_errors: Optional[List[str]] = None 