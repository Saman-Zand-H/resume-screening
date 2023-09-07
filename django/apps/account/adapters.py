from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.providers.google.views import (
    GoogleOAuth2Adapter as BaseGoogleOAuth2Adapter,
)

from .providers import GoogleProvider


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def get_provider(self, request, provider, client_id=None):
        if provider == "google":
            return GoogleProvider(request, self.get_app(request, provider, client_id))
        return super().get_provider(request, provider, client_id)


class GoogleOAuth2Adapter(BaseGoogleOAuth2Adapter):
    callback_url = "postmessage"

    def get_callback_url(self, *args, **kwargs):
        return self.callback_url
