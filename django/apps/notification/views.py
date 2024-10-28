from account.models import Profile, User
from common.utils import fields_join

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import QuerySet
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import FormView
from django.views.generic.detail import SingleObjectMixin

from .forms import CampaignNotifyUserForm, NotifyCampaignFilterForm
from .models import Campaign, CampaignNotification, Notification
from .senders import send_campaign_notifications


class BaseView(LoginRequiredMixin, UserPassesTestMixin, View):
    admin_site = None
    admin_title = None

    def test_func(self):
        return self.request.user.is_superuser

    def get_admin_title(self):
        return self.admin_title

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if not (admin_context := self.admin_site.each_context(self.request)):
            return context

        context.update(
            **admin_context,
            opts=self.model._meta,
            title=self.get_admin_title(),
            add=True,
        )
        return context


class CampaignNotifyView(BaseView, FormView, SingleObjectMixin):
    model = Campaign
    template_name = "notification/notify_user.html"
    form_class = CampaignNotifyUserForm
    admin_title = _("Notify Campaign")

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.object = self.get_object()

    def get_object(self, queryset=None) -> Campaign:
        return super().get_object(queryset)

    def get_form_kwargs(self):
        return super().get_form_kwargs() | {"campaign": self.get_object()}

    def get_success_url(self):
        return reverse_lazy(self.request.resolver_match.view_name, args=[self.get_object().pk])

    def get_filter_queryset(self):
        queryset = self.get_object().saved_filter.get_queryset()

        form_data = NotifyCampaignFilterForm(self.request.GET)
        if form_data.is_valid():
            queryset = queryset.filter(
                **{fields_join(Profile.user, User.email, "icontains"): form_data.cleaned_data.get("email")}
            )
        return queryset

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs, queryset=self.get_filter_queryset())

    def form_valid(self, form=None):
        users: QuerySet[User] = form.cleaned_data.get("users")
        campaign = self.get_object()
        send_campaign_notifications.delay(campaign_id=campaign.pk, pks=list(users.values_list("pk", flat=True)))

        return redirect(self.get_success_url())


class CampaginNotifyFailedView(BaseView, SingleObjectMixin, View):
    model = Campaign
    http_method_names = ["get"]

    def get_object(self, queryset=None) -> Campaign:
        return super().get_object(queryset)

    def get_success_url(self):
        return reverse_lazy("admin:notification_compaign_notify", args=[self.get_object().pk])

    def get(self, *args, **kwargs):
        failed_campaign_notifications = self.get_object().get_latest_failed_campaign_notifications()
        send_campaign_notifications(
            campaign_id=self.get_object().pk,
            pks=failed_campaign_notifications.values_list(
                fields_join(
                    CampaignNotification.notification,
                    Notification.user,
                    Profile.user.field.related_query_name(),
                    "pk",
                ),
                flat=True,
            ),
        )

        return redirect(self.get_success_url())


class CampaignNotifyAllView(CampaginNotifyFailedView):
    def get(self, *args, **kwargs):
        send_campaign_notifications(campaign_id=self.get_object().pk)

        return redirect(self.get_success_url())
