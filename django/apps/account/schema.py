import graphene
from graphql_auth import mutations as graphql_auth_mutations
from graphql_auth.constants import TokenAction
from graphql_auth.queries import MeQuery
from graphql_auth.utils import get_token, get_token_payload

from django.contrib.auth import get_user_model

from .forms import PasswordLessRegisterForm

User = get_user_model()


class Register(graphql_auth_mutations.Register):
    form = PasswordLessRegisterForm


class VerifyAccount(graphql_auth_mutations.VerifyAccount):
    token = graphene.String(description="The token required to set password after registration.")

    @classmethod
    def mutate(cls, *args, **kwargs):
        response = super().mutate(*args, **kwargs)
        if response.success:
            payload = get_token_payload(kwargs.get("token"), TokenAction.ACTIVATION, None)
            response.token = get_token(User.objects.get(**payload), TokenAction.PASSWORD_RESET)
        return response


class Query(MeQuery, graphene.ObjectType):
    pass


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


schema = graphene.Schema(query=Query, mutation=Mutation)
