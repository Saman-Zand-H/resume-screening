import os
import traceback
from abc import ABC, abstractmethod
from functools import lru_cache
from itertools import groupby
from typing import Dict, Generic, Optional, Type, TypeVar

import firebase_admin
from firebase_admin import messaging
from flex_blob.models import FileModel
from flex_blob.views import BlobResponseBuilder
from pydantic import BaseModel, ConfigDict
from twilio.rest import Client

from django.conf import settings
from django.core import mail
from django.core.mail import EmailMessage

from .models import (
    EmailNotification,
    InAppNotification,
    Notification,
    PushNotification,
    SMSNotification,
    UserDevice,
)

NT = TypeVar("NT", bound=Notification)


class NotificationContext(BaseModel, Generic[NT]):
    notification: NT
    context: dict = {}

    model_config = ConfigDict(arbitrary_types_allowed=True)


class NotificationSender(ABC):
    @abstractmethod
    def send(self, notification: NotificationContext, **kwargs):
        pass

    @abstractmethod
    def send_bulk(self, *notifications: NotificationContext, **kwargs):
        pass

    def handle_exception(self, exception: Exception, notification: NotificationContext) -> str:
        return f"{exception}\n{traceback.format_exc()}"

    def after_save(self, *notifications: NotificationContext):
        pass


class EmailNotificationSender(NotificationSender):
    def get_message(self, notification: NotificationContext[EmailNotification], from_email: str = None):
        email = EmailMessage(
            subject=notification.notification.title,
            from_email=from_email,
            to=[notification.notification.email],
            body=notification.notification.body,
        )
        email.content_subtype = "html"

        file_model_ids = notification.context.get("file_model_ids")

        if file_model_ids:
            blob_builder = BlobResponseBuilder.get_response_builder()
            for file_model_id in file_model_ids:
                attachment = FileModel.objects.get(pk=file_model_id)
                file_name = os.path.basename(blob_builder.get_file_name(attachment))
                email.attach(
                    file_name.split("/")[-1],
                    attachment.file.read(),
                    blob_builder.get_content_type(attachment),
                )
                attachment.file.close()

        return email

    def send(self, notification: NotificationContext[EmailNotification], **kwargs):
        email = self.get_message(notification, **kwargs)
        email.send()

    def send_bulk(self, *notifications: NotificationContext[EmailNotification], **kwargs):
        connection = mail.get_connection()
        emails = [self.get_message(notification, **kwargs) for notification in notifications]
        connection.send_messages(emails)


class SMSNotificationSender(NotificationSender):
    @classmethod
    @lru_cache
    def get_setting(cls, key: str, default: Optional[str] = None) -> str:
        return getattr(settings, "TWILIO", {}).get(key, default)

    @classmethod
    @lru_cache
    def get_client(cls) -> Client:
        return Client(cls.get_setting("ACCOUNT_SID"), cls.get_setting("AUTH_TOKEN"))

    def get_message(self, notification: NotificationContext[SMSNotification], from_number: Optional[str] = None):
        return {
            "body": notification.notification.body,
            "from_": from_number or self.get_setting("PHONE_NUMBER"),
            "to": notification.notification.phone_number.as_e164,
        }

    def send(self, notification: NotificationContext[SMSNotification], from_number: Optional[str] = None):
        client = self.get_client()
        client.messages.create(**self.get_message(notification, from_number=from_number))

    def send_bulk(self, *notifications: NotificationContext[SMSNotification], from_number: Optional[str] = None):
        client = self.get_client()
        for notification in notifications:
            client.messages.create(**self.get_message(notification, from_number=from_number))


class InAppNotificationSender(NotificationSender):
    def send(self, *args, **kwargs):
        pass

    def send_bulk(self, *args, **kwargs):
        pass


class PushNotificationSender(NotificationSender):
    @classmethod
    @lru_cache
    def setup(cls):
        firebase_admin.initialize_app()

    def get_message(self, notification: NotificationContext[PushNotification]):
        return messaging.Message(
            notification=messaging.Notification(
                title=notification.notification.title,
                body=notification.notification.body,
            ),
            token=notification.notification.device_token,
        )

    def send(self, notification: NotificationContext[PushNotification]):
        self.setup()
        messaging.send(self.get_message(notification))

    def send_bulk(self, *notifications: NotificationContext[PushNotification], **kwargs):
        self.setup()
        messages = [self.get_message(notification) for notification in notifications]
        responses = messaging.send_each(messages)

        for response, notification in zip(responses.responses, notifications):
            if not response.success and isinstance(response.exception, messaging.UnregisteredError):
                UserDevice.objects.filter(device_token=notification.notification.device_token).delete()

    def handle_exception(self, exception: Exception, notification: NotificationContext[PushNotification]):
        if isinstance(exception, messaging.UnregisteredError):
            UserDevice.objects.filter(device_token=notification.notification.device_token).delete()
        return super().handle_exception(exception, notification)


SENDERS: Dict[str, Type[NotificationSender]] = {
    EmailNotification: EmailNotificationSender,
    SMSNotification: SMSNotificationSender,
    InAppNotification: InAppNotificationSender,
    PushNotification: PushNotificationSender,
}


def send_notifications(*notifications: NotificationContext[Notification], **kwargs):
    notification_types = groupby(notifications, lambda n: type(n.notification))
    for notification_type, notification_group in notification_types:
        notification_contexts = list(notification_group)
        sender_class = SENDERS.get(notification_type)
        if not sender_class:
            continue

        sender = sender_class()
        try:
            if len(notification_contexts) == 1:
                sender.send(notification_contexts[0], **kwargs)
            else:
                sender.send_bulk(*notification_contexts, **kwargs)
            for notification in notification_contexts:
                notification.notification.set_status(Notification.Status.SENT)
            return True
        except Exception as e:
            for notification in notification_contexts:
                notification.notification.error = sender.handle_exception(e, notification)
                notification.notification.set_status(Notification.Status.FAILED)
            if settings.DEBUG:
                raise e
            return False
        finally:
            for notification in notification_contexts:
                notification.notification.save()
            sender.after_save(*notification_contexts)
    return False
