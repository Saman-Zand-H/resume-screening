from django.contrib import messages
from django.contrib.auth.views import LoginView
from django.http import HttpRequest
from django.shortcuts import redirect, resolve_url
from django.urls import reverse
from django.utils.translation import gettext as _

from .settings.constants import RecaptchaAction
from .utils import get_recaptcha_site_key, is_recaptcha_token_valid


class AdminLoginView(LoginView):
    template_name = "admin/recaptcha_login.html"

    def post(self, request: HttpRequest, *args, **kwargs):
        token = request.POST.get("g-recaptcha-response")
        if not is_recaptcha_token_valid(token, RecaptchaAction.login):
            messages.error(request, _("reCAPTCHA token is invalid"))
            return redirect(reverse("admin:login"))

        return super().post(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {"recaptcha_site_key": get_recaptcha_site_key(), "recaptcha_action": RecaptchaAction.login.value}
        )
        return context

    def get_default_redirect_url(self):
        if self.next_page:
            return resolve_url(self.next_page)
        else:
            return reverse("admin:index")
