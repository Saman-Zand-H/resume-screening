from dj_rest_auth.registration.views import SocialLoginView as BaseSocialLoginView

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
    callback_url = None
    callback_url = None
