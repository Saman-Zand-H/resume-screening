from enum import Enum


class Environment(Enum):
    LOCAL = "local"
    DEVELOPMENT = "development"
    STAGE = "stage"
    PRODUCTION = "production"


class Assistants:
    JOB = "get-available-jobs"
    SKILL = "get-or-create-skills"
    RESUME_JSON = "get-resume-json"
    GENERATE_RESUME = "get-resume-info"
    OCR = "get-file-text-content"
