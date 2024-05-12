from .production import *  # noqa
from .constants import Environment
import os

ENVIRONMENT_NAME = Environment.STAGE


# LOGGING = {
#     "version": 1,
#     "disable_existing_loggers": False,
#     "handlers": {
#         "gcs": {
#             "level": "ERROR",
#             "class": "config.log_handlers.GCSHandler",
#             "bucket_name": os.getenv("GCS_LOG_BUCKET_NAME", "django-logs"),
#             "log_file_name": os.getenv("GCS_LOG_FILE_NAME", "errors"),
#             "settings": os.getenv("DJANGO_SETTINGS_MODULE", "config.settings.local"),
#         },
#         "console": {
#             "level": "DEBUG",
#             "class": "logging.StreamHandler",
#         },
#     },
#     "loggers": {
#         "django": {
#             "handlers": ["gcs", "console"],
#             "level": "ERROR",
#             "propagate": True,
#         },
#         "graphql.error": {
#             "handlers": ["gcs", "console"],
#             "level": "ERROR",
#             "propagate": True,
#         },
#         "django.error": {
#             "handlers": ["gcs", "console"],
#             "level": "ERROR",
#             "propagate": True,
#         },
#     },
# }
