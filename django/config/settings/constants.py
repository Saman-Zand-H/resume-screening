from enum import Enum


class Environment(Enum):
    LOCAL = "local"
    DEVELOPMENT = "development"
    STAGE = "stage"
    PRODUCTION = "production"


class Assistants:
    JOB = "get-available-jobs"
    SKILL = "get-or-create-skills"
    FIND_RELATIVE_SKILLS = "find-relative-skills"
    RESUME_JSON = "get-resume-json"
    GENERATE_RESUME = "get-resume-info"
    DOCUMENT_VALIDATION = "document-validation"
    DOCUMENT_DATA_ANALYSIS = "analyze-document-data"
    LANGUAGE_CERTIFICATE_ANALYSIS = "language-certificate-analysis"
    OCR = "get-file-text-content"
