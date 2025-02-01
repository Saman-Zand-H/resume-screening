from collections.abc import Callable
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from google.cloud import vision
from pydantic import BaseModel, ConfigDict, Field


class FileType(Enum):
    IMAGE = "image"
    PDF = "pdf"
    DOCX = "docx"
    DOC = "doc"
    TXT = "txt"
    RTF = "rtf"
    OCR_REQUIRED = "ocr_required"


class EntityType(Enum):
    """Types of entities that can be extracted from resumes."""
    NAME = "name"
    JOB_TITLE = "job_title"
    COMPANY = "company"
    EDUCATION = "education"
    SKILL = "skill"
    DATE = "date"
    CERTIFICATION = "certification"
    LANGUAGE = "language"
    LOCATION = "location"
    EMAIL = "email"
    PHONE = "phone"
    URL = "url"
    SECTION_HEADER = "section_header"
    PROJECT = "project"


class AccuracyMetric(BaseModel):
    """Metrics for tracking the accuracy of entity extraction."""
    entity_type: EntityType
    correct_count: int = 0
    total_count: int = 0
    
    @property
    def accuracy(self) -> float:
        """Calculate the accuracy percentage."""
        if self.total_count == 0:
            return 0.0
        return (self.correct_count / self.total_count) * 100


class ResumeSection(Enum):
    """Major sections found in resumes."""
    PERSONAL_INFO = "personal_info"
    WORK_EXPERIENCE = "work_experience"
    EDUCATION = "education"
    SKILLS = "skills"
    PROJECTS = "projects"
    CERTIFICATIONS = "certifications"
    LANGUAGES = "languages"
    SUMMARY = "summary"


class Entity(BaseModel):
    """An entity extracted from a resume."""
    text: str
    entity_type: EntityType
    confidence: float
    normalized_value: Optional[str] = None
    section: Optional[ResumeSection] = None
    start_index: Optional[int] = None
    end_index: Optional[int] = None


class CachableVectorStore(BaseModel):
    id: str
    """The identifier of the vector store."""

    data_fn: Callable[[], List[Any]]
    """The function that returns the data to be stored in the vector store."""

    cache_key: str
    """The cache key for the vector store."""


class FileToTextResult(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    text: str
    file_type: FileType
    response: Union[vision.AnnotateImageResponse, vision.AnnotateFileResponse]


class ResumeAnalysisResult(BaseModel):
    """Results from analyzing a resume."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    entities: List[Entity] = Field(default_factory=list)
    sections: Dict[ResumeSection, str] = Field(default_factory=dict)
    raw_text: str
    language: str
    file_type: FileType
    processing_time_ms: int
    accuracy_metrics: Optional[Dict[EntityType, AccuracyMetric]] = None
