from allauth.socialaccount.providers.oauth2.client import (
    OAuth2Client as BaseOAuth2Client,
)


class OAuth2Client(BaseOAuth2Client):
    def __init__(self, *args, **kwargs):
        kwargs.pop("scope_delimiter", None)
        super().__init__(*args, **kwargs)
