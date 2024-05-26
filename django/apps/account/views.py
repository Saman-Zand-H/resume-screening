from dj_rest_auth.registration.views import SocialLoginView as BaseSocialLoginView

from .adapters import GoogleOAuth2Adapter, LinkedInOAuth2Adapter
from django.views import View
from django.http import HttpResponse
from cv.models import CVTemplate, GeneratedCV
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
        return HttpResponse(CVTemplate.objects.first().render(GeneratedCV.get_user_context(self.request.user)))
