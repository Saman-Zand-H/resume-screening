import graphene
from graphql_auth import mutations as graphql_auth_mutations
from graphql_auth.bases import SuccessErrorsOutput
from graphql_auth.constants import TokenAction
from graphql_auth.exceptions import EmailAlreadyInUseError
from graphql_auth.models import UserStatus
from graphql_auth.settings import graphql_auth_settings
from graphql_auth.utils import get_token, get_token_payload
from graphql_jwt.decorators import on_token_auth_resolve
from rest_framework.serializers import ValidationError

from django.contrib.auth import get_user_model
from django.utils import timezone

from .forms import PasswordLessRegisterForm
from .views import GoogleOAuth2View, LinkedInOAuth2View

User = get_user_model()


class Register(graphql_auth_mutations.Register):
    form = PasswordLessRegisterForm

    @classmethod
    def mutate(cls, *args, **kwargs):
        email = kwargs.get(User.EMAIL_FIELD)
        try:
            UserStatus.clean_email(email)
        except EmailAlreadyInUseError:
            user = User.objects.get(**{User.EMAIL_FIELD: email})
            if (
                not user.status.verified
                and user.last_login is None
                and user.date_joined + graphql_auth_settings.EXPIRATION_ACTIVATION_TOKEN < timezone.now()
            ):
                user.delete()

        return super().mutate(*args, **kwargs)


class VerifyAccount(graphql_auth_mutations.VerifyAccount):
    token = graphene.String(description="The token required to set password after registration with password_reset")

    @classmethod
    def mutate(cls, *args, **kwargs):
        response = super().mutate(*args, **kwargs)
        if response.success:
            payload = get_token_payload(kwargs.get("token"), TokenAction.ACTIVATION, None)
            response.token = get_token(User.objects.get(**payload), TokenAction.PASSWORD_RESET)
        return response


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
    register = Register.Field()
    verify_account = VerifyAccount.Field()
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
