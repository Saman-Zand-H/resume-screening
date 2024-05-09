from account.models import Resume
from account.tasks import set_user_resume_json
from cv.models import CVTemplate, GeneratedCV
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
        resume = Resume.objects.first()
        set_user_resume_json(resume.file.file.read(), resume.user.id)
        return HttpResponse("OK")
