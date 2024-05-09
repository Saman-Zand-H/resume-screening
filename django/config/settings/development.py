from .constants import Environment
from .production import *  # noqa
from .subscriptions import AccountSubscription

ENVIRONMENT_NAME = Environment.DEVELOPMENT
PUBSUB_SETTINGS["SUBSCRIPTIONS"] = ",".join([AccountSubscription.EMAILING.value])  # noqa
