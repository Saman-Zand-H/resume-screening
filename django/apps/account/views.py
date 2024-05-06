from cv.models import GeneratedCV
from dj_rest_auth.registration.views import SocialLoginView as BaseSocialLoginView

from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.views import View

from .adapters import GoogleOAuth2Adapter, LinkedInOAuth2Adapter
from .clients import OAuth2Client
from .serializers import SocialLoginSerializer


class SocialLoginView(BaseSocialLoginView):
    serializer_class = SocialLoginSerializer


class GoogleOAuth2View(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    client_class = OAuth2Client
    callback_url = GoogleOAuth2Adapter.callback_url


class LinkedInOAuth2View(SocialLoginView):
    adapter_class = LinkedInOAuth2Adapter
    client_class = OAuth2Client
    callback_url = None


class TestView(View):
    def get(self, *args, **kwargs):
        user = get_user_model().objects.first()
        pdf = GeneratedCV.from_user(user)
        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = 'attachment; filename="cv.pdf"'
        response.write(pdf)
        return response
