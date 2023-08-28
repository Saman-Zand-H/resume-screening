import logging
import os
from logging.config import dictConfig

from celery import Celery, signals

from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

app = Celery("connect")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.conf.broker_connection_retry_on_startup = True

if not settings.DEBUG:

    @signals.setup_logging.connect
    def on_celery_setup_logging(**kwargs):
        if log := getattr(settings, "LOGGING"):
            dictConfig(log)


app.autodiscover_tasks()
logger = logging.getLogger("celery")
