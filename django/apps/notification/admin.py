from account.models import User
from common.utils import fj
from flex_report.mixins import TablePageMixin

from django.contrib import admin
from django.db.models import QuerySet
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
    UserPushNotificationToken,
)
from .tasks import sync_campaign_scheduler_task
from .views import CampaginNotifyFailedView, CampaignNotifyAllView, CampaignNotifyView


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
        fj(CampaignNotification.notification, Notification.status),
        fj(
            CampaignNotification.campaign_notification_type,
            CampaignNotificationType.campaign,
        ),
    )
    list_filter = (
        fj(CampaignNotification.notification, Notification.status),
        fj(
            CampaignNotification.campaign_notification_type,
            CampaignNotificationType.notification_type,
        ),
    )
    autocomplete_fields = [
        fj(CampaignNotification.notification),
        fj(CampaignNotification.campaign_notification_type),
    ]
    search_fields = [
        fj(
            CampaignNotification.campaign_notification_type,
            CampaignNotificationType.campaign,
            Campaign.title,
        ),
        fj(
            CampaignNotification.notification,
            Notification.user,
            User.username,
        ),
        fj(
            CampaignNotification.notification,
            Notification.user,
            User.first_name,
        ),
        fj(
            CampaignNotification.notification,
            Notification.user,
            User.last_name,
        ),
    ]

    def lookup_allowed(self, lookup, value, request=None):
        if lookup == fj(
            CampaignNotification.campaign_notification_type,
            CampaignNotificationType.campaign,
            Campaign._meta.pk.attname,
        ):
            return True
        return super().lookup_allowed(lookup, value)


@admin.register(CampaignNotificationType)
class CampaignNotificationTypeAdmin(admin.ModelAdmin):
    list_display = (
        CampaignNotificationType.campaign.field.name,
        CampaignNotificationType.notification_type.field.name,
        CampaignNotificationType.body.field.name,
    )
    list_filter = (
        CampaignNotificationType.notification_type.field.name,
        CampaignNotificationType.campaign.field.name,
    )
    search_fields = (
        fj(CampaignNotificationType.campaign, Campaign.title),
        fj(CampaignNotificationType.body, NotificationTemplate.title),
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

    @admin.action(description=_("Sync All Scheduler"))
    def sync_schedulers(self, request, queryset: QuerySet[Campaign] = None):
        sync_campaign_scheduler_task()
        self.message_user(request, _("Campaigns synced with scheduler."))

    @admin.action(description=_("Activate Schedulers"))
    def activate_schedulers(self, request, queryset: QuerySet[Campaign]):
        queryset.update(**{fj(Campaign.is_scheduler_active): True})
        self.message_user(request, _("Schedulers activated."))

    @admin.action(description=_("Deactivate Schedulers"))
    def deactivate_schedulers(self, request, queryset: QuerySet[Campaign]):
        queryset.update(**{fj(Campaign.is_scheduler_active): False})
        self.message_user(request, _("Schedulers deactivated."))

    inlines = (CampaignNotificationTypeInline,)
    list_display = (
        Campaign.title.field.name,
        Campaign.modified.field.name,
        Campaign.created.field.name,
        Campaign.is_scheduler_active.field.name,
        action_buttons.__name__,
    )
    actions = [
        sync_schedulers.__name__,
        activate_schedulers.__name__,
        deactivate_schedulers.__name__,
    ]
    search_fields = (Campaign.title.field.name,)

    def get_urls(self):
        return super().get_urls() + [
            path(
                "<int:pk>/notify",
                self.admin_site.admin_view(CampaignNotifyView.as_view(admin_site=self.admin_site)),
                name="notification_compaign_notify",
            ),
            path(
                "<int:pk>/notify/all",
                self.admin_site.admin_view(CampaignNotifyAllView.as_view(admin_site=self.admin_site)),
                name="notification_compaign_notify_all",
            ),
            path(
                "<int:pk>/notify/failed",
                self.admin_site.admin_view(CampaginNotifyFailedView.as_view(admin_site=self.admin_site)),
                name="notification_compaign_notify_failed",
            ),
        ]


class BaseNotificationAdmin(admin.ModelAdmin):
    list_display = [
        Notification.user.field.name,
        Notification.created.field.name,
        Notification.status.field.name,
    ]
    list_filter = [
        Notification.status.field.name,
    ]
    search_fields = [
        fj(Notification.user, User.email),
    ]
    autocomplete_fields = [
        Notification.user.field.name,
    ]


@admin.register(Notification)
class NotificationAdmin(BaseNotificationAdmin):
    pass


@admin.register(EmailNotification)
class EmailNotificationAdmin(BaseNotificationAdmin):
    list_display = BaseNotificationAdmin.list_display + [
        EmailNotification.email.field.name,
        EmailNotification.title.field.name,
    ]


@admin.register(SMSNotification)
class SMSNotificationAdmin(BaseNotificationAdmin):
    list_display = BaseNotificationAdmin.list_display + [
        SMSNotification.phone_number.field.name,
    ]
    search_fields = BaseNotificationAdmin.search_fields + [
        SMSNotification.phone_number.field.name,
    ]


@admin.register(PushNotification)
class PushNotificationAdmin(BaseNotificationAdmin):
    list_display = BaseNotificationAdmin.list_display + [
        PushNotification.short_token.fget.__name__,
        PushNotification.title.field.name,
    ]
    search_fields = BaseNotificationAdmin.search_fields + [
        PushNotification.token.field.name,
        PushNotification.title.field.name,
    ]


@admin.register(InAppNotification)
class InAppNotificationAdmin(BaseNotificationAdmin):
    list_display = BaseNotificationAdmin.list_display + [
        InAppNotification.title.field.name,
    ]
    search_fields = BaseNotificationAdmin.search_fields + [
        InAppNotification.title.field.name,
        InAppNotification.read_at.field.name,
    ]


@admin.register(UserPushNotificationToken)
class UserPushNotificationTokenAdmin(admin.ModelAdmin):
    list_display = (
        UserPushNotificationToken.token.field.name,
        UserPushNotificationToken.device.field.name,
        UserPushNotificationToken.created.field.name,
    )
    search_fields = (
        UserPushNotificationToken.token.field.name,
        UserPushNotificationToken.device.field.name,
    )
    autocomplete_fields = (UserPushNotificationToken.device.field.name,)
