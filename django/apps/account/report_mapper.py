from notification.models import (
    EmailNotification,
    InAppNotification,
    PushNotification,
    SMSNotification,
    UserDevice,
)
from notification.report_mapper import register
from notification.types import NotificationTypes

from .models import Contact, Profile


@register(Profile, NotificationTypes.EMAIL)
def profile_email_mapper(instance: Profile):
    return [
        {
            EmailNotification.user.field.name: instance.user,
            EmailNotification.email.field.name: instance.user.email,
        }
    ]


@register(Profile, NotificationTypes.SMS)
def profile_sms_mapper(instance: Profile):
    return [
        {
            SMSNotification.user.field.name: instance.user,
            SMSNotification.phone_number.field.name: phone_number.value,
        }
        for phone_number in instance.user.get_contacts_by_type(Contact.Type.PHONE)
    ]


@register(Profile, NotificationTypes.PUSH)
def profile_push_mapper(instance: Profile):
    return [
        {
            PushNotification.user.field.name: instance.user,
            PushNotification.device_token.field.name: device.device_token,
        }
        for device in UserDevice.objects.filter(**{UserDevice.user.field.name: instance.user})
    ]


@register(Profile, NotificationTypes.IN_APP)
def profile_in_app_mapper(instance: Profile):
    return [{InAppNotification.user.field.name: instance.user}]
