import graphene
from graphql_auth import mutations as graphql_auth_mutations
from graphql_auth.bases import SuccessErrorsOutput
from graphql_auth.constants import TokenAction
from graphql_auth.utils import get_token, get_token_payload
from graphql_jwt.decorators import on_token_auth_resolve
from rest_framework.serializers import ValidationError

from django.contrib.auth import get_user_model

from .forms import PasswordLessRegisterForm
from .views import GoogleOAuth2View

User = get_user_model()


class Register(graphql_auth_mutations.Register):
    form = PasswordLessRegisterForm


class VerifyAccount(graphql_auth_mutations.VerifyAccount):
    token = graphene.String(description="The token required to set password after registration with password_reset")

    @classmethod
    def mutate(cls, *args, **kwargs):
        response = super().mutate(*args, **kwargs)
        if response.success:
            payload = get_token_payload(kwargs.get("token"), TokenAction.ACTIVATION, None)
            response.token = get_token(User.objects.get(**payload), TokenAction.PASSWORD_RESET)
        return response


class GoogleAuth(SuccessErrorsOutput, graphene.Mutation):
    class Arguments:
        code = graphene.String(required=True)

    token = graphene.String()
    refresh_token = graphene.String()

    @classmethod
    def mutate(cls, root, info, code, **kwargs):
        data = {"code": code}
        try:
            auth = GoogleOAuth2View.serializer_class(
                data=data, context={"view": GoogleOAuth2View, "request": info.context}
            ).validate(data)
        except ValidationError as e:
            return cls(success=False, errors={"code": e.detail})
        on_token_auth_resolve((info.context, auth.get("user"), cls))
        cls.success = True
        cls.errors = None
        return cls


class LinkedInAuth(SuccessErrorsOutput, graphene.Mutation):
    class Arguments:
        code = graphene.String(required=True)

    token = graphene.String()
    refresh_token = graphene.String()

    @classmethod
    def mutate(cls, root, info, code, **kwargs):
        data = {"code": code}

        # try:
        #     auth = GoogleOAuth2View.serializer_class(
        #         data=data, context={"view": GoogleOAuth2View, "request": info.context}
        #     ).validate(data)
        # except ValidationError as e:
        #     return cls(success=False, errors={"code": e.detail})
        # on_token_auth_resolve((info.context, auth.get("user"), cls))
        cls.success = True
        cls.errors = None
        return cls


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
    # linkedin_auth = LinkedInAuth.Field()
