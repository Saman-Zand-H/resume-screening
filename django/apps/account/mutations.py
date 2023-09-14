import graphene
from graphql_auth import mutations as graphql_auth_mutations
from graphql_auth.bases import SuccessErrorsOutput
from graphql_jwt.decorators import on_token_auth_resolve
from rest_framework.serializers import ValidationError

from django.contrib.auth import get_user_model

from .views import GoogleOAuth2View, LinkedInOAuth2View

User = get_user_model()


class BaseSocialAuth(SuccessErrorsOutput, graphene.Mutation):
    class Arguments:
        code = graphene.String(required=True)

    token = graphene.String()
    refresh_token = graphene.String()

    @classmethod
    def setup(cls, root, info, **kwargs):
        return NotImplemented

    @classmethod
    def mutate(cls, root, info, **kwargs):
        payload = cls.setup(root, info, **kwargs)
        data = payload.get("data")
        view = payload.get("view")

        try:
            auth = view.serializer_class(data=data, context={"view": view, "request": info.context}).validate(data)
        except ValidationError as e:
            return cls(success=False, errors={"code": e.detail})

        user = auth.get("user")
        user.status.verified = True
        user.status.save(update_fields=["verified"])
        on_token_auth_resolve((info.context, user, cls))
        cls.success = True
        cls.errors = None
        return cls


class GoogleAuth(BaseSocialAuth):
    @classmethod
    def setup(cls, root, info, code):
        return {"data": {"code": code}, "view": GoogleOAuth2View}


class LinkedInAuth(BaseSocialAuth):
    class Arguments(BaseSocialAuth.Arguments):
        redirect_uri = graphene.String(required=True)

    @classmethod
    def setup(cls, root, info, code, **kwargs):
        return {
            "data": {"code": code},
            "view": type("View", (LinkedInOAuth2View,), {"callback_url": kwargs.get("redirect_uri")}),
        }


class Mutation(graphene.ObjectType):
    register = graphql_auth_mutations.Register.Field()
    verify_account = graphql_auth_mutations.VerifyAccount.Field()
    resend_activation_email = graphql_auth_mutations.ResendActivationEmail.Field()
    send_password_reset_email = graphql_auth_mutations.SendPasswordResetEmail.Field()
    password_reset = graphql_auth_mutations.PasswordReset.Field()
    password_change = graphql_auth_mutations.PasswordChange.Field()
    token_auth = graphql_auth_mutations.ObtainJSONWebToken.Field()
    verify_token = graphql_auth_mutations.VerifyToken.Field()
    refresh_token = graphql_auth_mutations.RefreshToken.Field()
    revoke_token = graphql_auth_mutations.RevokeToken.Field()
    google_auth = GoogleAuth.Field()
    linkedin_auth = LinkedInAuth.Field()
