import importlib

from django.conf import settings


def import_attribute(path):
    assert isinstance(path, str)
    module_path, attr_name = path.rsplit(".", 1)
    module = importlib.import_module(module_path)
    return getattr(module, attr_name)


def get_setting(name, default):
    return settings.PUBSUB_SETTINGS.get(name, default)


class AppSettings:
    def _setting(self, name, default):
        return get_setting(name, default) or default

    @property
    def BACKEND_CLASS(self):
        backend_class_path = self._setting("BACKEND_CLASS", "flex_pubsub.backends.LocalPubSubBackend")
        return import_attribute(backend_class_path)

    @property
    def SCHEDULER_BACKEND_CLASS(self):
        scheduler_backend_class_path = self._setting(
            "SCHEDULER_BACKEND_CLASS",
            "flex_pubsub.scheduler.LocalSchedulerBackend",
        )
        return import_attribute(scheduler_backend_class_path)

    @property
    def GOOGLE_CREDENTIALS(self):
        credentials = self._setting("GOOGLE_CREDENTIALS", None)
        if credentials:
            if isinstance(credentials, str):
                from google.oauth2 import service_account

                return service_account.Credentials.from_service_account_file(credentials)
            return credentials
        return None

    @property
    def GOOGLE_PROJECT_ID(self):
        return self._setting("GOOGLE_PROJECT_ID", None)

    @property
    def TOPIC_NAME(self):
        return self._setting("TOPIC_NAME", "default-topic")

    @property
    def TOPIC_PATH(self):
        return f"projects/{self.GOOGLE_PROJECT_ID}/topics/{self.TOPIC_NAME}"

    @property
    def SCHEDULER_LOCATION(self):
        return self._setting("SCHEDULER_LOCATION", "us-central1")

    @property
    def CLOUD_RUN_SERVICE_URL(self):
        return self._setting("CLOUD_RUN_SERVICE_URL", None)

    @property
    def LISTENER_PORT(self):
        return self._setting("LISTENER_PORT", 8001)

    @property
    def SUBSCRIPTIONS(self):
        return list(map(str.strip, filter(bool, self._setting("SUBSCRIPTIONS", "").strip().split(","))))


app_settings = AppSettings()
