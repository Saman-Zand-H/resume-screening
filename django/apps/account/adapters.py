from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.providers.google.views import (
    GoogleOAuth2Adapter as BaseGoogleOAuth2Adapter,
)
from allauth.socialaccount.providers.openid_connect.provider import (
    OpenIDConnectProvider as BaseOpenIDConnectProvider,
)
from allauth.socialaccount.providers.openid_connect.views import (
    OpenIDConnectOAuth2Adapter as BaseOpenIDConnectOAuth2Adapter,
)

from .providers import GoogleProvider


class OpenIDConnectProvider(BaseOpenIDConnectProvider):
    def get_scope(self, *args, **kwargs):
        return super().get_scope()


PROVIDERS = {
    "google": GoogleProvider,
    "linkedin": OpenIDConnectProvider,
}


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def get_provider(self, request, **kwargs):
        if provider := PROVIDERS.get(kwargs.get("provider")):
            return provider(request, self.get_app(request, **kwargs))
        return super().get_provider(request, **kwargs)


class GoogleOAuth2Adapter(BaseGoogleOAuth2Adapter):
    callback_url = "postmessage"

    def get_callback_url(self, *args, **kwargs):
        return self.callback_url


class LinkedInOAuth2Adapter(BaseOpenIDConnectOAuth2Adapter):
    def __init__(self, request):
        self.provider_id = "linkedin"
        super().__init__(request, self.provider_id)
