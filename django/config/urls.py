from apps.api.schema import schema
from graphene_file_upload.django import FileUploadGraphQLView as GraphQLView

from django.conf import settings
from django.contrib import admin, messages
from django.contrib.auth.views import LoginView
from django.http import HttpRequest
from django.shortcuts import redirect
from django.urls import include, path, reverse
from django.views.decorators.csrf import csrf_exempt
from django.utils.translation import gettext as _

from .utils import create_recaptcha_assessment


class CustomAdminLoginView(LoginView):
    template_name = "admin/login.html"

    def post(self, request: HttpRequest, *args, **kwargs):
        token = request.POST.get("g-recaptcha-response")
        assessment = create_recaptcha_assessment(token, "LOGIN")
        if not assessment:
            messages.error(request, _("reCAPTCHA token is invalid"))
            return redirect(reverse("admin:login"))

        if assessment.risk_analysis.score < 0.7:
            messages.error(request, _("reCAPTCHA score is too low"))
            return redirect(reverse("admin:login"))

        return super().post(request, *args, **kwargs)


urlpatterns = [
    path("admin/", admin.site.urls),
    path("graphql", csrf_exempt(GraphQLView.as_view(graphiql=settings.DEBUG, schema=schema))),
    path("criteria/", include("criteria.urls"), name="criteria"),
    path("academy/", include("academy.urls"), name="academy"),
    path("media/", include("flex_blob.urls"), name="blob"),
]

if not settings.DEBUG:
    urlpatterns = [path("admin/login/", CustomAdminLoginView.as_view(), name="admin_login"), *urlpatterns]
