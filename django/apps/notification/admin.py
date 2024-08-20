from django.contrib import admin

from .models import (
    EmailNotification,
    InAppNotification,
    Notification,
    PushNotification,
    SMSNotification,
    UserDevice,
)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        Notification.user.field.name,
        Notification.created.field.name,
        Notification.status.field.name,
    )
    list_filter = (Notification.status.field.name,)
    search_fields = (Notification.user.field.name,)
    autocomplete_fields = (Notification.user.field.name,)


@admin.register(EmailNotification)
class EmailNotificationAdmin(admin.ModelAdmin):
    list_display = (
        EmailNotification.email.field.name,
        EmailNotification.title.field.name,
        EmailNotification.user.field.name,
        EmailNotification.created.field.name,
        EmailNotification.status.field.name,
    )
    list_filter = (EmailNotification.status.field.name,)
    search_fields = (
        EmailNotification.email.field.name,
        EmailNotification.title.field.name,
        EmailNotification.user.field.name,
    )
    autocomplete_fields = (EmailNotification.user.field.name,)


@admin.register(SMSNotification)
class SMSNotificationAdmin(admin.ModelAdmin):
    list_display = (
        SMSNotification.phone_number.field.name,
        SMSNotification.user.field.name,
        SMSNotification.created.field.name,
        SMSNotification.status.field.name,
    )
    list_filter = (SMSNotification.status.field.name,)
    search_fields = (
        SMSNotification.phone_number.field.name,
        SMSNotification.user.field.name,
    )
    autocomplete_fields = (SMSNotification.user.field.name,)


@admin.register(PushNotification)
class PushNotificationAdmin(admin.ModelAdmin):
    list_display = (
        PushNotification.device_token.field.name,
        PushNotification.title.field.name,
        PushNotification.user.field.name,
        PushNotification.created.field.name,
        PushNotification.status.field.name,
    )
    list_filter = (PushNotification.status.field.name,)
    search_fields = (
        PushNotification.device_token.field.name,
        PushNotification.title.field.name,
        PushNotification.user.field.name,
    )
    autocomplete_fields = (PushNotification.user.field.name,)


@admin.register(InAppNotification)
class InAppNotificationAdmin(admin.ModelAdmin):
    list_display = (
        InAppNotification.title.field.name,
        InAppNotification.user.field.name,
        InAppNotification.created.field.name,
        InAppNotification.status.field.name,
        InAppNotification.read_at.field.name,
    )
    list_filter = (InAppNotification.status.field.name,)
    search_fields = (InAppNotification.title.field.name, InAppNotification.user.field.name)
    autocomplete_fields = (InAppNotification.user.field.name,)


@admin.register(UserDevice)
class UserDeviceAdmin(admin.ModelAdmin):
    list_display = (UserDevice.device_token.field.name, UserDevice.user.field.name, UserDevice.created.field.name)
    search_fields = (UserDevice.device_token.field.name, UserDevice.user.field.name)
    autocomplete_fields = (UserDevice.user.field.name,)
