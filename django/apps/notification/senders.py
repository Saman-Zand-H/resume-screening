import os
import traceback
from abc import ABC, abstractmethod
from functools import lru_cache
from itertools import groupby
from typing import Generic, Optional, TypeVar, Union

import firebase_admin
from common.utils import get_all_subclasses
from firebase_admin import messaging
from flex_blob.models import FileModel
from flex_blob.views import BlobResponseBuilder
from pydantic import BaseModel, ConfigDict
from twilio.rest import Client

from django.conf import settings
from django.core import mail
from django.core.mail import EmailMessage

from .constants import NotificationTypes
from .context_mapper import ContextMapperRegistry
from .models import (
    Campaign,
    CampaignNotification,
    EmailNotification,
    Notification,
    PushNotification,
    SMSNotification,
    UserDevice,
    WhatsAppNotification,
)
from .report_mapper import ReportMapper
from .types import NotificationType

NT = TypeVar("NT", bound=Notification)


class NotificationContext(BaseModel, Generic[NT]):
    notification: NT
    context: Optional[dict] = {}

    model_config = ConfigDict(arbitrary_types_allowed=True)


class NotificationSender(ABC):
    notification_type: NotificationType

    @classmethod
    def get_senders_dict(cls):
        return {
            sender.notification_type: sender
            for sender in get_all_subclasses(cls)
            if getattr(sender, "notification_type", None)
        }

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
    notification_type = NotificationTypes.EMAIL

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


class TwilioSender(NotificationSender):
    @classmethod
    @lru_cache
    def get_setting(cls, key: str, default: Optional[str] = None) -> str:
        return getattr(settings, "TWILIO", {}).get(key, default)

    @classmethod
    @lru_cache
    def get_client(cls) -> Client:
        return Client(cls.get_setting("ACCOUNT_SID"), cls.get_setting("AUTH_TOKEN"))

    @abstractmethod
    @lru_cache
    def serialize_phone_number(cls, phone_number: str) -> str:
        pass

    @abstractmethod
    @lru_cache
    def get_default_from_number(cls) -> str:
        pass

    def get_message(
        self,
        notification: NotificationContext[Union[SMSNotification, WhatsAppNotification]],
        from_number: Optional[str] = None,
    ):
        return {
            "body": notification.notification.body,
            "from_": self.serialize_phone_number(from_number or self.get_default_from_number()),
            "to": self.serialize_phone_number(notification.notification.phone_number.as_e164),
        }

    def send(self, notification: Union[SMSNotification, WhatsAppNotification], from_number: Optional[str] = None):
        client = self.get_client()
        client.messages.create(**self.get_message(notification, from_number=from_number))

    def send_bulk(
        self,
        *notifications: Union[SMSNotification, WhatsAppNotification],
        from_number: Optional[str] = None,
    ):
        client = self.get_client()
        for notification in notifications:
            client.messages.create(**self.get_message(notification, from_number=from_number))


class SMSNotificationSender(TwilioSender):
    notification_type = NotificationTypes.SMS

    @classmethod
    @lru_cache
    def serialize_phone_number(cls, phone_number: str) -> str:
        return phone_number

    @classmethod
    @lru_cache
    def get_default_from_number(cls) -> str:
        return cls.get_setting("PHONE_NUMBER")


class WhatsAppNotificationSender(TwilioSender):
    notification_type = NotificationTypes.WHATSAPP

    @classmethod
    @lru_cache
    def serialize_phone_number(cls, phone_number: str) -> str:
        return f"whatsapp:{phone_number}"

    @classmethod
    @lru_cache
    def get_default_from_number(cls) -> str:
        return cls.get_setting("WHATSAPP_NUMBER")


class InAppNotificationSender(NotificationSender):
    notification_type = NotificationTypes.IN_APP

    def send(self, *args, **kwargs):
        pass

    def send_bulk(self, *args, **kwargs):
        pass


class PushNotificationSender(NotificationSender):
    notification_type = NotificationTypes.PUSH

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


def send_notifications(*notifications: NotificationContext[Notification], **kwargs) -> list[bool]:
    notification_types = groupby(notifications, lambda n: n.notification.notification_type.value)
    for notification_type, notification_group in notification_types:
        notification_contexts = list(notification_group)
        sender_class = NotificationSender.get_senders_dict().get(notification_type)
        if not sender_class:
            continue

        sender = sender_class()
        try:
            send_method = sender.send if len(notification_contexts) == 1 else sender.send_bulk
            send_method(*notification_contexts, **kwargs)

            for notification in notification_contexts:
                notification.notification.set_status(Notification.Status.SENT)

        except Exception as e:
            for notification in notification_contexts:
                notification.notification.error = sender.handle_exception(e, notification)
                notification.notification.set_status(Notification.Status.FAILED)

            if not settings.DEBUG:
                raise e

        finally:
            for notification in notification_contexts:
                notification.notification.save()
            sender.after_save(*notification_contexts)
    return map(lambda n: n.notification.status == Notification.Status.SENT, notifications)


def send_campaign_notifications(campaign: Campaign, queryset=None):
    campaign_notification_types = campaign.get_campaign_notification_types()
    report_qs = queryset or campaign.saved_filter.get_queryset()
    notification_contexts = []
    campaign_notifications = []

    notification_dict = Notification.get_notifications_dict()
    for campaign_notification_type in campaign_notification_types:
        notification_type = campaign_notification_type.notification_type
        NotificationModel = notification_dict.get(notification_type)

        notifications_kwargs = []
        for instance in report_qs:
            context = ContextMapperRegistry.get_context(instance)
            body = campaign_notification_type.notification_template.render(context)
            notifications_kwargs.extend(
                notification_kwargs | {Notification.body.field.name: body}
                for notification_kwargs in ReportMapper.map(instance, notification_type)
            )

        for kwargs in notifications_kwargs:
            notification_context = NotificationContext(notification=NotificationModel(**kwargs))
            notification_contexts.append(notification_context)
            campaign_notifications.append(
                CampaignNotification(
                    campaign_notification_type=campaign_notification_type,
                    notification=notification_context.notification,
                )
            )

    send_notifications(*notification_contexts)
    CampaignNotification.objects.bulk_create(campaign_notifications, batch_size=20)
