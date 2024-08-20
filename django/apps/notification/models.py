from account.models import User
from model_utils.models import TimeStampedModel
from phonenumber_field.modelfields import PhoneNumberField

from django.db import models
from django.utils.translation import gettext_lazy as _


def token_excerpt(token: str) -> str:
    return f"{token[:10]}...{token[-10:]}"


class NotificationTitle(models.Model):
    title = models.CharField(max_length=255, verbose_name=_("Title"))

    class Meta:
        abstract = True


class Notification(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", _("Pending")
        SENT = "sent", _("Sent")
        FAILED = "failed", _("Failed")

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications", verbose_name=_("User"))
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

    class Meta:
        verbose_name = _("Notification")
        verbose_name_plural = _("Notifications")


class EmailNotification(NotificationTitle, Notification):
    email = models.EmailField(verbose_name=_("Email"))

    class Meta:
        verbose_name = _("Email Notification")
        verbose_name_plural = _("Email Notifications")

    def __str__(self):
        return self.email


class SMSNotification(Notification):
    phone_number = PhoneNumberField(verbose_name=_("Phone Number"))

    class Meta:
        verbose_name = _("SMS Notification")
        verbose_name_plural = _("SMS Notifications")

    def __str__(self):
        return self.phone_number.as_e164


class PushNotification(NotificationTitle, Notification):
    device_token = models.CharField(max_length=255, verbose_name=_("Device Token"))

    class Meta:
        verbose_name = _("Push Notification")
        verbose_name_plural = _("Push Notifications")

    def __str__(self):
        return token_excerpt(self.device_token)


class UserDevice(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="devices", verbose_name=_("User"))
    device_token = models.CharField(max_length=255, verbose_name=_("Device Token"))

    class Meta:
        verbose_name = _("User Device")
        verbose_name_plural = _("User Devices")

    def __str__(self):
        return token_excerpt(self.device_token)


class InAppNotification(NotificationTitle, Notification):
    read_at = models.DateTimeField(verbose_name=_("Read At"), blank=True, null=True)

    class Meta:
        verbose_name = _("In App Notification")
        verbose_name_plural = _("In App Notifications")
