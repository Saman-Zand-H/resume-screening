from common.utils import fields_join, get_all_subclasses
from croniter import croniter
from flex_report.models import TemplateSavedFilter
from model_utils.models import TimeStampedModel
from phonenumber_field.modelfields import PhoneNumberField

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.template.base import Template
from django.template.context import Context
from django.template.loader import get_template
from django.utils.translation import gettext_lazy as _

from .constants import NotificationTypes
from .context_mapper import ContextMapperRegistry
from .types import NotificationType


def token_excerpt(token: str) -> str:
    return f"{token[:10]}...{token[-10:]}"


def get_template_help_text():
    return "<br/><hr/><br/>".join(
        f"<b>{model._meta.verbose_name}</b>: <br/><br/>{'<br/>'.join(f'{{{{ {mapper.name} }}}}: {mapper.help}' for mapper in mappers)}"
        for model, mappers in ContextMapperRegistry.registry().items()
    )


def get_campaign_crontab_help_text():
    return "If you wish to make this campaign periodic, then go to <a href='https://crontab.guru/'>Crontab Halper</a> and copy-paste the crontab values."


class NotificationTemplate(TimeStampedModel):
    title = models.CharField(max_length=255, verbose_name=_("Title"))
    content_template = models.TextField(verbose_name=_("Content Template"), help_text=get_template_help_text)

    def render(self, context: dict, is_email=False) -> str:
        content = Template(self.content_template).render(Context(context))
        if is_email:
            base_template = get_template("notification/email_base.html").template
            content = Template(base_template.source.replace("REPLACE_ME", content)).render(Context(context))
        return content

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = _("Notification Template")
        verbose_name_plural = _("Notification Templates")


class Campaign(TimeStampedModel):
    crontab = models.CharField(
        max_length=255,
        verbose_name=_("Crontab"),
        help_text=get_campaign_crontab_help_text(),
        blank=True,
        null=True,
    )
    crontab_last_run = models.DateTimeField(
        verbose_name=_("Crontab Last Run"),
        blank=True,
        null=True,
    )
    sent_at = models.DateTimeField(verbose_name=_("Sent At"), blank=True, null=True)
    title = models.CharField(max_length=255, verbose_name=_("Title"))
    saved_filter = models.ForeignKey(
        TemplateSavedFilter,
        on_delete=models.CASCADE,
        related_name="campaigns",
        verbose_name=_("Saved Filter"),
    )

    def clean(self):
        if self.crontab and not croniter.is_valid(self.crontab):
            raise ValidationError({fields_join(Campaign.crontab): _("Invalid crontab value.")})

    def get_campaign_notification_types(self):
        campaign_notification_manager: models.BaseManager[CampaignNotificationType] = getattr(
            self,
            CampaignNotificationType.campaign.field.related_query_name(),
        )
        return campaign_notification_manager.all()

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = _("Campaign")
        verbose_name_plural = _("Campaigns")


class CampaignNotificationType(TimeStampedModel):
    notification_type = models.CharField(
        max_length=10,
        choices=NotificationTypes.choices,
        verbose_name=_("Notification Type"),
    )
    subject = models.ForeignKey(
        NotificationTemplate,
        on_delete=models.CASCADE,
        related_name="campaign_notification_subjects",
        verbose_name=_("Subject"),
        null=True,
        blank=True,
    )
    body = models.ForeignKey(
        NotificationTemplate,
        on_delete=models.CASCADE,
        related_name="campaign_notification_bodies",
        verbose_name=_("Body"),
    )
    campaign = models.ForeignKey(
        Campaign,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name=_("Campaign"),
    )

    SUBJECT_REQUIRED_TYPES = [
        NotificationTypes.EMAIL,
        NotificationTypes.PUSH,
        NotificationTypes.IN_APP,
    ]

    def clean(self):
        subject_required = self.notification_type in self.SUBJECT_REQUIRED_TYPES
        if subject_required and not self.subject:
            raise ValidationError(
                {
                    CampaignNotificationType.subject.field.name: _(
                        "Notification Title is required for the selected notification type."
                    )
                }
            )
        elif not subject_required and self.subject:
            raise ValidationError(
                {
                    CampaignNotificationType.subject.field.name: _(
                        "Notification Title is not required for the selected notification type."
                    )
                }
            )

    def __str__(self):
        return f"{self.campaign} - {self.notification_type}"

    class Meta:
        verbose_name = _("Campaign Notification Type")
        verbose_name_plural = _("Campaign Notification Types")
        unique_together = [
            ("notification_type", "campaign"),
        ]


class NotificationTitle(models.Model):
    title = models.TextField(verbose_name=_("Title"))

    def __str__(self):
        return self.title

    class Meta:
        abstract = True


class Notification(TimeStampedModel):
    notification_type: NotificationType

    class Status(models.TextChoices):
        PENDING = "pending", _("Pending")
        SENT = "sent", _("Sent")
        FAILED = "failed", _("Failed")

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name=_("User"),
    )
    body = models.TextField(verbose_name=_("Body"))
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        verbose_name=_("Status"),
        default=Status.PENDING.value,
    )
    error = models.TextField(verbose_name=_("Error"), blank=True, null=True)

    def set_status(self, status: Status):
        self.status = status

    def __str__(self):
        return str(self.user)

    @classmethod
    def get_notifications_dict(cls):
        return {notification.notification_type: notification for notification in get_all_subclasses(cls)}

    class Meta:
        verbose_name = _("Notification")
        verbose_name_plural = _("Notifications")


class CampaignNotification(TimeStampedModel):
    campaign_notification_type = models.ForeignKey(
        CampaignNotificationType,
        on_delete=models.CASCADE,
        related_name="campaign_notifications",
        verbose_name=_("Campaign Notification Type"),
    )
    notification = models.OneToOneField(
        Notification,
        on_delete=models.CASCADE,
        related_name="campaign_notifications",
        verbose_name=_("Notification"),
        blank=True,
        null=True,
    )

    def __str__(self):
        return f"{self.campaign_notification_type} - {self.notification}"

    class Meta:
        verbose_name = _("Campaign Notification")
        verbose_name_plural = _("Campaign Notification")


class EmailNotification(NotificationTitle, Notification):
    notification_type = NotificationTypes.EMAIL

    email = models.EmailField(verbose_name=_("Email"))

    class Meta:
        verbose_name = _("Email Notification")
        verbose_name_plural = _("Email Notifications")

    def __str__(self):
        return self.email


class SMSNotification(Notification):
    notification_type = NotificationTypes.SMS

    phone_number = PhoneNumberField(verbose_name=_("Phone Number"))

    class Meta:
        verbose_name = _("SMS Notification")
        verbose_name_plural = _("SMS Notifications")

    def __str__(self):
        return self.phone_number.as_e164


class WhatsAppNotification(Notification):
    notification_type = NotificationTypes.WHATSAPP

    phone_number = PhoneNumberField(verbose_name=_("Phone Number"))

    class Meta:
        verbose_name = _("WhatsApp Notification")
        verbose_name_plural = _("WhatsApp Notifications")

    def __str__(self):
        return self.phone_number.as_e164


class DeviceToken(models.Model):
    device_token = models.CharField(max_length=255, verbose_name=_("Device Token"))

    class Meta:
        abstract = True

    def __str__(self):
        return token_excerpt(self.device_token)

    @property
    def short_token(self):
        return token_excerpt(self.device_token)


class PushNotification(DeviceToken, NotificationTitle, Notification):
    notification_type = NotificationTypes.PUSH

    class Meta:
        verbose_name = _("Push Notification")
        verbose_name_plural = _("Push Notifications")

    def __str__(self):
        return self.short_token


class UserDevice(DeviceToken, TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="devices",
        verbose_name=_("User"),
    )

    class Meta:
        verbose_name = _("User Device")
        verbose_name_plural = _("User Devices")

    def __str__(self):
        return self.short_token


class InAppNotification(NotificationTitle, Notification):
    notification_type = NotificationTypes.IN_APP

    read_at = models.DateTimeField(verbose_name=_("Read At"), blank=True, null=True)

    class Meta:
        verbose_name = _("In App Notification")
        verbose_name_plural = _("In App Notifications")
