from common.utils import fields_join
from flex_report.mixins import TablePageMixin

from django.contrib import admin
from django.template.loader import get_template
from django.urls import path
from django.utils.translation import gettext_lazy as _

from .models import (
    Campaign,
    CampaignNotification,
    CampaignNotificationType,
    EmailNotification,
    InAppNotification,
    Notification,
    NotificationTemplate,
    PushNotification,
    SMSNotification,
    UserDevice,
    WhatsAppNotification,
)
from .views import CampaignNotifyView, CampaignUserNotifyView


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = (
        NotificationTemplate.title.field.name,
        NotificationTemplate.created.field.name,
        NotificationTemplate.modified.field.name,
    )


@admin.register(CampaignNotification)
class CampaignNotificationAdmin(admin.ModelAdmin):
    list_display = (
        CampaignNotification.campaign_notification_type.field.name,
        CampaignNotification.notification.field.name,
        CampaignNotification.created.field.name,
        fields_join(CampaignNotification.notification, Notification.status),
    )
    list_filter = (
        fields_join(CampaignNotification.notification, Notification.status),
        fields_join(
            CampaignNotification.campaign_notification_type,
            CampaignNotificationType.campaign,
            Campaign.title,
        ),
        fields_join(
            CampaignNotification.campaign_notification_type,
            CampaignNotificationType.campaign,
            Campaign._meta.pk.attname,
        ),
        fields_join(
            CampaignNotification.campaign_notification_type,
            CampaignNotificationType.notification_type,
        ),
    )
    search_fields = [
        fields_join(
            CampaignNotification.campaign_notification_type,
            CampaignNotificationType.campaign,
            Campaign.title,
        ),
    ]


@admin.register(CampaignNotificationType)
class CampaignNotificationTypeAdmin(admin.ModelAdmin):
    list_display = (
        CampaignNotificationType.campaign.field.name,
        CampaignNotificationType.notification_type.field.name,
        CampaignNotificationType.notification_template.field.name,
    )
    list_filter = (
        CampaignNotificationType.notification_type.field.name,
        CampaignNotificationType.campaign.field.name,
    )
    search_fields = (
        fields_join(CampaignNotificationType.campaign, Campaign.title),
        fields_join(CampaignNotificationType.notification_template, NotificationTemplate.title),
        CampaignNotificationType.notification_type.field.name,
    )
    autocomplete_fields = (CampaignNotificationType.campaign.field.name,)


class CampaignNotificationTypeInline(admin.TabularInline):
    model = CampaignNotificationType
    extra = 0


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    @admin.display(description=_("Action"))
    def action_buttons(self, obj):
        return get_template("notification/action_buttons.html").render(
            {
                "obj": obj,
                "saved_filter_keyword": TablePageMixin.saved_filter_keyword,
            }
        )

    inlines = (CampaignNotificationTypeInline,)
    list_display = (
        Campaign.title.field.name,
        Campaign.modified.field.name,
        Campaign.created.field.name,
        action_buttons.__name__,
    )
    search_fields = (Campaign.title.field.name,)

    def get_urls(self):
        return super().get_urls() + [
            path(
                "<int:pk>/notify",
                self.admin_site.admin_view(CampaignNotifyView.as_view(admin_site=self.admin_site)),
                name="notification_compaign_notify",
            ),
            path(
                "<int:pk>/notify/user",
                self.admin_site.admin_view(CampaignUserNotifyView.as_view(admin_site=self.admin_site)),
                name="notification_compaign_notify_user",
            ),
        ]


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


@admin.register(WhatsAppNotification)
class WhatsAppNotificationAdmin(admin.ModelAdmin):
    list_display = (
        WhatsAppNotification.phone_number.field.name,
        WhatsAppNotification.user.field.name,
        WhatsAppNotification.created.field.name,
        WhatsAppNotification.status.field.name,
    )
    list_filter = (WhatsAppNotification.status.field.name,)
    search_fields = (
        WhatsAppNotification.phone_number.field.name,
        WhatsAppNotification.user.field.name,
    )
    autocomplete_fields = (WhatsAppNotification.user.field.name,)


@admin.register(PushNotification)
class PushNotificationAdmin(admin.ModelAdmin):
    list_display = (
        PushNotification.short_token.fget.__name__,
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
