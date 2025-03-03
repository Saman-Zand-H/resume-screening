"""
Django settings for config project.

Generated by 'django-admin startproject' using Django 5.1.1.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""

import os
import sys
from datetime import timedelta
from pathlib import Path

import environ
import sentry_sdk
from corsheaders.defaults import default_headers
from import_export.formats.base_formats import XLSX
from sentry_sdk.integrations.django import DjangoIntegration

from django.core.exceptions import DisallowedHost

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, os.path.join(BASE_DIR, "apps"))

env = environ.Env()
ENV_FILE_PATH = os.environ.get("ENV_FILE_PATH", os.path.join(BASE_DIR.parent, ".env"))

env.read_env(ENV_FILE_PATH)

GOOGLE_APPLICATION_CREDENTIALS = os.environ.get("GOOGLE_CLOUD_CREDENTIALS") or None
GOOGLE_CLOUD_PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT")
GOOGLE_CLOUD_LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")

if GOOGLE_APPLICATION_CREDENTIALS:
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GOOGLE_APPLICATION_CREDENTIALS
else:
    GOOGLE_APPLICATION_CREDENTIALS = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get("SECRET_KEY") or "django-insecure-xbtb+fr8279na3c!&$1ud^tfwh^7u+7#1=#@odrkhct-@!e$_2"

# Application definition

INSTALLED_APPS = [
    "markdownfield",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
    "graphene_django",
    "allauth",
    "allauth.account",
    "rest_framework",
    "rest_framework.authtoken",
    "dj_rest_auth",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "allauth.socialaccount.providers.openid_connect",
    "django_extensions",
    "django_filters",
    "graphql_auth",
    "graphql_jwt.refresh_token.apps.RefreshTokenConfig",
    "cachalot",
    "corsheaders",
    "rules.apps.AutodiscoverRulesConfig",
    "import_export",
    "colorfield",
    "sortedm2m",
    "cities_light",
    "phonenumber_field",
    "computedfields",
    "flex_pubsub",
    "flex_blob",
    "flex_eav",
    "flex_report",
    "flex_observer",
]

INSTALLED_APPS += [
    "common",
    "api",
    "cv",
    "ai",
    "criteria",
    "score",
    "academy",
    "account",
    "notification",
]

MIDDLEWARE = [
    "common.middlewares.DjangoErrorHandlingMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "account.middlewares.AuthMiddleware",
    "account.middlewares.DeviceMiddleware",
]


ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.request",
                "common.context_processors.now",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    "default": env.db("DB_URL", "postgres://job_seekers_api:job_seekers_api@127.0.0.1:5432/job_seekers_api"),
}


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATICFILES_DIRS = (os.path.join(BASE_DIR, "static/"),)
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "assets"
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")
FAVICON_ROOT = os.path.join(BASE_DIR, "assets", "favicons")

GOOGLE_CLOUD_BUCKET_NAME = os.environ.get("GOOGLE_CLOUD_BUCKET_NAME")
GOOGLE_CLOUD_STATIC_BUCKET_NAME = os.environ.get("GOOGLE_CLOUD_STATIC_BUCKET_NAME")
if GOOGLE_CLOUD_BUCKET_NAME and GOOGLE_CLOUD_STATIC_BUCKET_NAME:
    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.gcloud.GoogleCloudStorage",
            "OPTIONS": {
                "bucket_name": GOOGLE_CLOUD_BUCKET_NAME,
            },
        },
        "staticfiles": {
            "BACKEND": "storages.backends.gcloud.GoogleCloudStorage",
            "OPTIONS": {
                "bucket_name": GOOGLE_CLOUD_STATIC_BUCKET_NAME,
            },
        },
    }


# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "auth_account.User"

AUTHENTICATION_BACKENDS = [
    "rules.permissions.ObjectPermissionBackend",
    "graphql_auth.backends.GraphQLAuthBackend",
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]


GRAPHENE = {
    "SCHEMA": "api.schema.schema",
    "MIDDLEWARE": [
        "graphql_jwt.middleware.JSONWebTokenMiddleware",
        "common.middlewares.GrapheneErrorHandlingMiddleware",
    ],
}

GRAPHQL_JWT = {
    "JWT_AUTH_HEADER_PREFIX": "Bearer",
    "JWT_VERIFY_EXPIRATION": True,
    "JWT_LONG_RUNNING_REFRESH_TOKEN": True,
    "JWT_EXPIRATION_DELTA": timedelta(minutes=5),
    "JWT_REFRESH_EXPIRATION_DELTA": timedelta(days=7),
    "JWT_GET_USER_BY_NATURAL_KEY_HANDLER": "graphql_auth.utils.get_user_by_natural_key",
    "JWT_ALLOW_ANY_CLASSES": [
        "graphql_auth.mutations.Register",
        "graphql_auth.mutations.VerifyAccount",
        "graphql_auth.mutations.ResendActivationEmail",
        "graphql_auth.mutations.SendPasswordResetEmail",
        "graphql_auth.mutations.PasswordReset",
        "graphql_auth.mutations.ObtainJSONWebToken",
        "graphql_auth.mutations.VerifyToken",
        "graphql_auth.mutations.RefreshToken",
        "graphql_auth.mutations.RevokeToken",
    ],
}


GRAPHQL_AUTH = {
    "LOGIN_ALLOWED_FIELDS": ["email"],
    "ALLOW_LOGIN_NOT_VERIFIED": False,
    "ALLOW_LOGIN_WITH_SECONDARY_EMAIL": False,
    "ALLOW_PASSWORDLESS_REGISTRATION": True,
    "REGISTER_MUTATION_FIELDS": ["email", "first_name", "last_name"],
    "EXPIRATION_ACTIVATION_TOKEN": timedelta(hours=1),
    "EXPIRATION_PASSWORD_RESET_TOKEN": timedelta(minutes=15),
    "EMAIL_ASYNC_TASK": "account.tasks.graphql_auth_async_email",
}


SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "APPS": [
            {
                "client_id": os.environ.get("GOOGLE_OAUTH_CLIENT_ID"),
                "secret": os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET"),
                "key": "",
            },
        ],
        "SCOPE": [
            "profile",
            "email",
        ],
        "AUTH_PARAMS": {
            "access_type": "online",
        },
    },
    "openid_connect": {
        "APPS": [
            {
                "provider_id": "linkedin",
                "name": "LinkedIn",
                "client_id": os.environ.get("LINKEDIN_OAUTH_CLIENT_ID"),
                "secret": os.environ.get("LINKEDIN_OAUTH_CLIENT_SECRET"),
                "settings": {
                    "server_url": "https://www.linkedin.com/oauth",
                },
            }
        ]
    },
}
SOCIALACCOUNT_ADAPTER = "account.adapters.SocialAccountAdapter"
HEADLESS_ONLY = True

CITIES_LIGHT_CITY_SOURCES = ["https://download.geonames.org/export/dump/cities500.zip"]

CRITERIA_SETTINGS = {
    "BASE_URL": os.environ.get("CRITERIA_BASE_URL", "https://integrations.criteriacorp.com/api/v1"),
    "AUTH_TOKEN": os.environ.get("CRITERIA_AUTH_TOKEN"),
    "AUTH_TYPE": os.environ.get("CRITERIA_AUTH_TYPE", "Bearer"),
    "WEBHOOK_SECRET": os.environ.get("CRITERIA_WEBHOOK_SECRET"),
}

PUBSUB_SETTINGS = {
    "GOOGLE_CREDENTIALS": GOOGLE_APPLICATION_CREDENTIALS,
    "GOOGLE_PROJECT_ID": GOOGLE_CLOUD_PROJECT,
    "TOPIC_NAME": os.environ.get("GOOGLE_PUBSUB_TOPIC_NAME"),
    "SUBSCRIPTIONS": os.environ.get("GOOGLE_PUBSUB_SUBSCRIPTIONS"),
    "LISTENER_PORT": os.environ.get("PORT", os.environ.get("PUBSUB_LISTENER_PORT")),
    "BACKEND_CLASS": os.environ.get("GOOGLE_PUBSUB_BACKEND_CLASS"),
    "SCHEDULER_BACKEND_CLASS": os.environ.get("GOOGLE_PUBSUB_SCHEDULER_BACKEND_CLASS"),
    "ON_RUN_SUB_CALLBACK": "notification.tasks.on_run_sub_callback",
}

SILENCED_SYSTEM_CHECKS = ["cachalot.W001"]

DATA_UPLOAD_MAX_NUMBER_FIELDS = None

SITE_DOMAIN = os.environ.get("SITE_DOMAIN", "http://localhost:8000")

ACADEMY_SETTINGS = {
    "BASE_URL": os.environ.get("ACADEMY_BASE_URL"),
    "USERNAME": os.environ.get("ACADEMY_USERNAME"),
    "PASSWORD": os.environ.get("ACADEMY_PASSWORD"),
    "WEBHOOK_SECRET": os.environ.get("ACADEMY_WEBHOOK_SECRET"),
}

EXPORT_FORMATS = [XLSX]

TWILIO = {
    "ACCOUNT_SID": os.environ.get("TWILIO_ACCOUNT_SID"),
    "API_KEY": os.environ.get("TWILIO_API_KEY"),
    "API_SECRET": os.environ.get("TWILIO_API_SECRET"),
    "PHONE_NUMBER": os.environ.get("TWILIO_PHONE_NUMBER"),
}

REPORT_BASE_VIEW = "common.views.FlexBaseView"
REPORT_MODEL_ADMINS = {
    "Template": "common.admin.TemplateAdmin",
}
REPORT_VIEWS = {"TEMPLATE_DELETE": "common.views.flex_template_delete_view"}
REPORT_FILTERSET_CLASS = "common.filterset.FilterSet"


CORS_ALLOW_HEADERS = (
    *default_headers,
    "x-cpj-device-id",
    "sentry-trace",
    "baggage",
)

VALID_EMAIL_CALLBACK_URLS = os.environ.get("VALID_EMAIL_CALLBACK_URLS", "cpjcompany.com,cpj.ai").split(",")

SENTRY_DSN = os.environ.get("SENTRY_DSN")
if SENTRY_DSN:

    def before_send(event, hint):
        exc_info = hint.get("exc_info", [None])[0]
        log_record = hint.get("log_record")

        if exc_info is DisallowedHost or getattr(log_record, "sentry_ignore", False):
            return None

        return event

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        send_default_pii=True,
        traces_sample_rate=1.0,
        profiles_sample_rate=1.0,
        _experiments={
            "continuous_profiling_auto_start": True,
        },
        integrations=[
            DjangoIntegration(cache_spans=True),
        ],
        environment=f"js-api-{os.environ.get('DJANGO_SETTINGS_MODULE')}",
        attach_stacktrace=True,
        before_send=before_send,
        keep_alive=True,
    )


RECAPTCHA_SITE_KEY = os.environ.get("GOOGLE_CLOUD_RECAPTCHA_SITE_KEY")
