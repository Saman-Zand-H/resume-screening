from allauth.socialaccount.providers.google.provider import (
    GoogleProvider as BaseGoogleProvider,
)


class GoogleProvider(BaseGoogleProvider):
    def get_scope(self, *args, **kwargs):
        return super().get_scope()
