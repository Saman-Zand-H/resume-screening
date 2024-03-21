import logging
from concurrent.futures import CancelledError, TimeoutError
from operator import call
from typing import Any, Callable, Dict, Type

try:
    from google.api_core.exceptions import NotFound
    from google.cloud import pubsub_v1
except ImportError:
    pubsub_v1 = None

from .app_settings import app_settings
from .types import RequestMessage

logger = logging.getLogger("pubsub")


class Singleton(type):
    _instances: Dict[Type, Any] = {}

    def __call__(cls, *args: Any, **kwargs: Any) -> Any:
        if cls not in cls._instances or kwargs.get("force_new_instance", False):
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class BaseBackend(metaclass=Singleton):
    def publish(self, message: RequestMessage) -> None:
        raise NotImplementedError

    def subscribe(self, callback: Callable[[str], None]) -> None:
        raise NotImplementedError


class LocalPubSubBackend(BaseBackend):
    def publish(self, raw_message: RequestMessage):
        from .tasks import task_registry

        logger.info(f"Publishing message: {raw_message}")

        message = RequestMessage.model_validate_json(raw_message)
        if not (task := task_registry.get_task(task_name := message.task_name)):
            raise ValueError(f"Task '{task_name}' not found.")

        call(task, *message.args, **message.kwargs)

    def subscribe(self, callback: Callable[[str], None]) -> None:
        logger.info("Subscribing to local pub/sub")
        ...


class GooglePubSubBackend(BaseBackend):
    def __init__(self) -> None:
        if pubsub_v1 is None:
            raise ImportError("google-cloud-pubsub is not installed.")
        credentials = app_settings.GOOGLE_CREDENTIALS
        project_id = app_settings.GOOGLE_PROJECT_ID

        self.subscriber = pubsub_v1.SubscriberClient(credentials=credentials)
        self.publisher = pubsub_v1.PublisherClient(credentials=credentials)
        self.subscription_path = self.subscriber.subscription_path(project_id, app_settings.SUBSCRIPTION_NAME)
        self.topic_path = self.publisher.topic_path(project_id, app_settings.TOPIC_NAME)
        logger.info("Initialized GooglePubSubBackend")

    def publish(self, message: RequestMessage) -> None:
        logger.info(f"Publishing message: {message}")

        request_message = RequestMessage.model_validate_json(message)
        try:
            self.publisher.get_topic(request={"topic": self.topic_path})
        except NotFound:
            logger.warning(f"Topic not found: {self.topic_path}. Creating topic.")
            self.publisher.create_topic(request={"name": self.topic_path})

        logger.info(f"Publishing message to topic {self.topic_path}")
        self.publisher.publish(self.topic_path, request_message.model_dump_json().encode("utf-8"))

    def subscribe(self, callback: Callable[[str], None]) -> None:
        try:
            self.subscriber.get_subscription(request={"subscription": self.subscription_path})
        except NotFound:
            logger.warning(f"Subscription not found: {self.subscription_path}. Creating subscription.")
            self.subscriber.create_subscription(request={"name": self.subscription_path, "topic": self.topic_path})

        logger.info(f"Subscribing to {self.subscription_path}")
        streaming_pull_future = self.subscriber.subscribe(
            self.subscription_path,
            callback=self._wrap_callback(callback),
        )

        try:
            streaming_pull_future.result()
        except (CancelledError, TimeoutError):
            logger.error("Subscription was cancelled or timed out")
            streaming_pull_future.cancel()
            raise

    def _wrap_callback(self, callback: Callable[[str], None]) -> Callable[..., None]:
        """
        Wrap the callback function to handle message acknowledgment.

            :param callback: The callback function to be wrapped.

            :return: The wrapped callback function.
        """

        def _callback(message: "pubsub_v1.subscriber.message.Message") -> None:  # type: ignore
            callback(message.data.decode("utf-8"))
            message.ack()

        return _callback
