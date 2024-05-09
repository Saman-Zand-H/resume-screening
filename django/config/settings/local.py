from .base import *  # noqa
from .constants import Environment

ENVIRONMENT_NAME = Environment.LOCAL

DEBUG = True
ALLOWED_HOSTS = ["*"]
CORS_ALLOW_ALL_ORIGINS = True

CACHALOT_ENABLED = False

SESSION_ENGINE = "django.contrib.sessions.backends.db"

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
