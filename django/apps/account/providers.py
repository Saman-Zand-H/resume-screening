from allauth.socialaccount.providers.google.provider import (
    GoogleProvider as BaseGoogleProvider,
)
from allauth.socialaccount.providers.openid_connect.provider import (
    OpenIDConnectProvider as BaseOpenIDConnectProvider,
)


class ProviderMixin:
    def get_scope(self, *args, **kwargs):
        return super().get_scope()


class GoogleProvider(ProviderMixin, BaseGoogleProvider):
    pass


class LinkedInProvider(ProviderMixin, BaseOpenIDConnectProvider):
    pass
