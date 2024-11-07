from django.contrib import messages
from django.contrib.auth.views import LoginView
from django.http import HttpRequest
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext as _

from .settings.constants import RecaptchaAction
from .utils import is_recaptcha_token_valid


class AdminLoginView(LoginView):
    template_name = "admin/login.html"

    def post(self, request: HttpRequest, *args, **kwargs):
        token = request.POST.get("g-recaptcha-response")
        if not is_recaptcha_token_valid(token, RecaptchaAction.login):
            messages.error(request, _("reCAPTCHA token is invalid"))
            return redirect(reverse("admin:login"))

        return super().post(request, *args, **kwargs)
