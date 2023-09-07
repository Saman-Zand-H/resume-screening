from dj_rest_auth.registration.views import SocialLoginView

from .adapters import GoogleOAuth2Adapter, LinkedInOAuth2Adapter
from .clients import OAuth2Client


class GoogleOAuth2View(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    client_class = OAuth2Client
    callback_url = GoogleOAuth2Adapter.callback_url


class LinkedInOAuth2View(SocialLoginView):
    adapter_class = LinkedInOAuth2Adapter
    client_class = OAuth2Client
    callback_url = None
