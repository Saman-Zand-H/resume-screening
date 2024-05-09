from django.apps import AppConfig


class CvConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'cv'
    
    def ready(self):
        from . import tasks  # noqa: F401
