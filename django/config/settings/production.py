import os

from .base import *  # noqa
from .constants import Environment

ENVIRONMENT_NAME = Environment.PRODUCTION

DEBUG = os.environ.get("DEBUG", "False") == "True"

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.environ.get("EMAIL_HOST")
EMAIL_PORT = 587
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")
EMAIL_USE_TLS = True

DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

ALLOWED_HOSTS = [SITE_DOMAIN]  # noqa

CORS_ALLOWED_ORIGIN_URLS = list(
    set(filter(bool, os.environ.get("CORS_ALLOWED_ORIGIN_URLS", "").split(",") + [os.environ.get("FRONTEND_URL")]))
)
if CORS_ALLOWED_ORIGIN_URLS:
    CORS_ALLOWED_ORIGINS = CORS_ALLOWED_ORIGIN_URLS
else:
    CORS_ALLOW_ALL_ORIGINS = True

# SSL Configuration
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_ENGINE = "django.contrib.sessions.backends.cache"

# Redis
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": f"{os.environ.get('REDIS_URL', 'redis://localhost:6379')}",
    }
}

GRAPHQL_AUTH["EMAIL_ASYNC_TASK"] = "account.tasks.graphql_auth_async_email"  # noqa

GOOGLE_CLOUD_ERROR_BUCKET_NAME = os.environ.get("GOOGLE_CLOUD_ERROR_BUCKET_NAME")

if GOOGLE_CLOUD_ERROR_BUCKET_NAME:
    MIDDLEWARE = ["common.middlewares.DjangoErrorHandlingMiddleware"] + MIDDLEWARE  # noqa
    LOGGING = {
        "version": 1,
        "disable_existing_loggers": False,
        "handlers": {
            "gcs": {
                "level": "ERROR",
                "class": "config.log_handlers.GCSHandler",
                "bucket_name": GOOGLE_CLOUD_ERROR_BUCKET_NAME,
                "log_file_name": "errors",
            },
            "console": {
                "level": "DEBUG",
                "class": "logging.StreamHandler",
            },
        },
        "loggers": {
            "django": {
                "handlers": ["gcs", "console"],
                "level": "ERROR",
                "propagate": True,
            },
            "graphql.error": {
                "handlers": ["gcs", "console"],
                "level": "ERROR",
                "propagate": True,
            },
            "django.error": {
                "handlers": ["gcs", "console"],
                "level": "ERROR",
                "propagate": True,
            },
        },
    }
