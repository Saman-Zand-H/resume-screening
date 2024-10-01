import contextlib
import json
import logging

from flex_report.defaults.views import BaseView as BaseFlexBaseView
from flex_report.defaults.views import (
    ReportView as BaseReportView,
)
from flex_report.defaults.views import (
    TemplateCreateCompleteView as BaseTemplateCreateCompleteView,
)
from flex_report.defaults.views import (
    TemplateCreateInitView as BaseTemplateCreateInitView,
)
from flex_report.defaults.views import TemplateDeleteView
from flex_report.defaults.views import (
    TemplateSavedFilterCreateView as BaseTemplateSavedFilterCreateView,
)
from flex_report.defaults.views import (
    TemplateSavedFilterUpdateView as BaseTemplateSavedFilterUpdateView,
)
from flex_report.defaults.views import (
    TemplateUpdateView as BaseTemplateUpdateView,
)

from django.contrib.admin.sites import AdminSite
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.edit import FormView

from .forms import WebhookForm
from .webhook import WebhookEvent, WebhookHandler

logger = logging.getLogger(__name__)


class FlexAdminBaseView:
    admin_site = None
    admin_title = None

    def __init__(self, admin_site=None, *args, **kwargs):
        self.admin_site = admin_site
        super().__init__(*args, **kwargs)

    def get_success_url(self):
        return self.success_url

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


class TemplateReportView(FlexAdminBaseView, BaseReportView):
    def get_admin_title(self):
        return self.get_template().title


class TemplateCreateInitView(FlexAdminBaseView, BaseTemplateCreateInitView):
    admin_title = _("Template Wizard")

    def get_success_url(self):
        return reverse_lazy("admin:flex_report_template_wizard_complete", kwargs={"pk": self.object.pk})


class TemplateSavedFilterCreateView(FlexAdminBaseView, BaseTemplateSavedFilterCreateView):
    admin_title = _("Create Filter")
    success_url = reverse_lazy("admin:flex_report_template_changelist")

    def get_success_url(self):
        return self.success_url


class TemplateSavedFilterUpdateView(FlexAdminBaseView, BaseTemplateSavedFilterUpdateView):
    admin_title = _("Update Filter")
    template_name = "flex_report/template_saved_filter_create.html"

    def get_success_url(self):
        return reverse_lazy("admin:flex_report_template_report", args=[self.get_object().pk])


class TemplateUpdateView(FlexAdminBaseView, BaseTemplateUpdateView):
    admin_title = _("Update Template")
    template_name = "flex_report/template_create_complete.html"
    success_url = reverse_lazy("admin:flex_report_template_changelist")


class TemplateCreateCompleteView(FlexAdminBaseView, BaseTemplateCreateCompleteView):
    admin_title = _('Complete "%(template_name)s"')
    success_url = reverse_lazy("admin:flex_report_template_changelist")

    def get_admin_title(self):
        return self.admin_title % {"template_name": self.object}


class FlexBaseView(UserPassesTestMixin, BaseFlexBaseView, AdminSite):
    def get_context_data(self, **kwargs):
        return super().get_context_data(
            **kwargs,
            is_popup=False,
            is_nav_sidebar_enabled=True,
            has_permission=True,
            app_list=self.get_app_list(self.request),
        )

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_superuser


class FlexTemplateDeleteView(FlexBaseView, TemplateDeleteView):
    success_url = reverse_lazy("admin:flex_report_template_changelist")

    def get(self, *args, **kwargs):
        self.get_object().delete()
        return redirect(self.success_url)


flex_template_delete_view = FlexTemplateDeleteView.as_view()


class WebhookView(FormView):
    event: WebhookEvent
    form_class: WebhookForm

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        with contextlib.suppress(json.JSONDecodeError):
            kwargs["data"] = json.loads(self.request.body.decode("utf-8"))
        return kwargs

    def get_error(self, message, status=400):
        return JsonResponse({"error": message}, status=status)

    def get_response(self, data, status=200):
        return JsonResponse(data, status=status)

    def get_webhook_secret(self):
        raise NotImplementedError

    def get_webhook_header_key(self):
        raise NotImplementedError

    def post(self, request, *args, **kwargs):
        api_key = request.headers.get(self.get_webhook_header_key())
        if api_key is None or api_key != self.get_webhook_secret():
            return self.get_error("Unauthorized", status=401)
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        payload = form.cleaned_data
        try:
            payload_data = WebhookHandler.handle_event(self.event, payload)
            return self.get_response(payload_data)
        except ValueError as e:
            logger.error(f"Event handling error: {e}")
            return self.get_error(str(e))
        except Exception as e:
            logger.error(f"Failed to process webhook: {e}")
            return self.get_error("Failed to process webhook", status=500)

    def form_invalid(self, form):
        return self.get_error("Invalid form data")
