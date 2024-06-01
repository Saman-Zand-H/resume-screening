from enum import Enum


class Environment(Enum):
    LOCAL = "local"
    DEVELOPMENT = "development"
    STAGE = "stage"
    PRODUCTION = "production"


class Assistants:
    JOB = "job"
    SKILL = "skill"
    RESUME = "resume"
    HEADLINES = "headlines"
    GENERATE_RESUME = "generate-resume"
