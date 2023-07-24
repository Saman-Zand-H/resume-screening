from .base import *  # noqa

DEBUG = True
ALLOWED_HOSTS = ["*"]

SESSION_ENGINE = "django.contrib.sessions.backends.db"

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
