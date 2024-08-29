from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import FormView
from django.views.generic.detail import SingleObjectMixin

from .forms import CampaignNotifyConfirmForm, CampaignNotifyUserForm
from .models import Campaign
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


class CampaignUserNotifyView(BaseView, FormView, SingleObjectMixin):
    model = Campaign
    template_name = "notification/notify_user.html"
    form_class = CampaignNotifyUserForm

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.object = self.get_object()

    def get_form_kwargs(self):
        return super().get_form_kwargs() | {"campaign": self.get_object()}

    def get_success_url(self):
        return reverse_lazy("admin:notification_campaign_changelist")

    def form_valid(self, form=None):
        users = form.cleaned_data.get("users")
        campaign = self.get_object()
        send_campaign_notifications(campaign, queryset=users)

        return redirect(self.get_success_url())


class CampaignNotifyView(BaseView, FormView, SingleObjectMixin):
    model = Campaign
    form_class = CampaignNotifyConfirmForm
    template_name = "notification/campaign_send_confirm.html"

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.object = self.get_object()

    def get_success_url(self):
        return reverse_lazy("admin:notification_campaign_changelist")

    def get(self, request, *args, **kwargs):
        return self.form_valid()

    def form_valid(self, form=None):
        campaign = self.get_object()
        send_campaign_notifications(campaign)

        return redirect(self.get_success_url())
