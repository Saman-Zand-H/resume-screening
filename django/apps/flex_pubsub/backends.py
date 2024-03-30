import http
import http.server
import logging
from operator import call
from typing import Any, Callable, Dict, Type

try:
    from google.api_core.exceptions import NotFound
    from google.cloud import pubsub_v1
except ImportError:
    pubsub_v1 = None

from .app_settings import app_settings
from .tasks import task_registry
from .types import CallbackContext, RequestMessage, SubscriptionCallback

logger = logging.getLogger("flex_pubsub")


class Singleton(type):
    _instances: Dict[Type, Any] = {}

    def __call__(cls, *args, **kwargs) -> Any:
        if cls not in cls._instances or kwargs.get("force_new_instance", False):
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class BaseBackend(metaclass=Singleton):
    def publish(self, message: RequestMessage) -> None:
        raise NotImplementedError

    def subscribe(self, callback: Callable[[CallbackContext], None], task: Callable) -> None:
        raise NotImplementedError

    def subscribe_tasks(self, callback: Callable[[CallbackContext], None]) -> None:
        for task in task_registry.get_all_tasks().values():
            self.subscribe(callback, task)


class LocalPubSubBackend(BaseBackend):
    def publish(self, raw_message: RequestMessage):
        from .tasks import task_registry

        logger.info(f"Publishing message: {raw_message}")

        message = RequestMessage.model_validate_json(raw_message)
        if not (task := task_registry.get_task(task_name := message.task_name)):
            raise ValueError(f"Task '{task_name}' not found.")

        call(task, *message.args, **message.kwargs)

    def subscribe(self, *args, **kwargs) -> None:
        logger.info("Subscribing to local pub/sub (Doing nothing)")


class GooglePubSubBackend(BaseBackend):
    def __init__(self) -> None:
        if pubsub_v1 is None:
            raise ImportError("google-cloud-pubsub is not installed.")
        credentials = app_settings.GOOGLE_CREDENTIALS
        project_id = app_settings.GOOGLE_PROJECT_ID

        self.subscriber = pubsub_v1.SubscriberClient(credentials=credentials)
        self.publisher = pubsub_v1.PublisherClient(credentials=credentials)
        self.subscriptions = {
            subscription_name: self.subscriber.subscription_path(project_id, subscription_name)
            for subscription_name in app_settings.SUBSCRIPTIONS
        }
        self.topic_path = self.publisher.topic_path(project_id, app_settings.TOPIC_NAME)
        logger.info("Initialized GooglePubSubBackend")

    def run_server(
        self,
        server_class=http.server.HTTPServer,
        handler_class=http.server.BaseHTTPRequestHandler,
        port=app_settings.LISTENER_PORT,
    ):
        server_address = ("", port)
        httpd = server_class(server_address, handler_class)
        logger.info(f"Starting server on port {port}")
        httpd.serve_forever()

    def publish(self, message: RequestMessage) -> None:
        logger.info(f"Publishing message: {message}")

        request_message = RequestMessage.model_validate_json(message)
        self._ensure_topic_exists()

        logger.info(f"Publishing message to topic {self.topic_path}")
        self.publisher.publish(self.topic_path, request_message.model_dump_json().encode("utf-8"))

    def subscribe(self, callback: SubscriptionCallback, task: Callable) -> None:
        for subscription_name, subscription_path in self.subscriptions.items():
            if subscription_name not in task.subscriptions:
                continue
            self._ensure_subscription_exists(subscription_path)
            logger.info(f"Subscribing to {subscription_path}")
            self.subscriber.subscribe(
                subscription_path,
                callback=self._wrap_callback(callback, task),
            )

        self.run_server()

    def _wrap_callback(self, callback: SubscriptionCallback, task: Callable) -> Callable[[str], None]:
        from google.cloud.pubsub_v1.subscriber.message import Message

        def _callback(message: Message) -> None:
            context = CallbackContext(raw_message=message.data.decode("utf-8"), ack=message.ack, task=task)
            callback(context)

        return _callback

    def _ensure_topic_exists(self) -> None:
        try:
            self.publisher.get_topic(request={"topic": self.topic_path})
        except NotFound:
            logger.warning(f"Topic not found: {self.topic_path}. Creating topic.")
            self.publisher.create_topic(request={"name": self.topic_path})

    def _ensure_subscription_exists(self, subscription_path: str) -> None:
        try:
            self.subscriber.get_subscription(request={"subscription": subscription_path})
        except NotFound:
            logger.warning(f"Subscription not found: {subscription_path}. Creating subscription.")
            self.subscriber.create_subscription(request={"name": subscription_path, "topic": self.topic_path})
