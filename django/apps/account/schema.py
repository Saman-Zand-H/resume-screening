import graphene
from graphql_auth import mutations as graphql_auth_mutations
from graphql_auth.forms import PasswordLessRegisterForm as PasswordLessRegisterFormBase
from graphql_auth.queries import MeQuery

from django.contrib.auth.hashers import make_password


class PasswordLessRegisterForm(PasswordLessRegisterFormBase):
    def clean(self):
        self.cleaned_data["password1"] = self.cleaned_data["password2"] = make_password(None)
        return super().clean()


class Register(graphql_auth_mutations.Register):
    form = PasswordLessRegisterForm


class Query(MeQuery, graphene.ObjectType):
    pass


class Mutation(graphene.ObjectType):
    register = Register.Field()
    verify_account = graphql_auth_mutations.VerifyAccount.Field()
    resend_activation_email = graphql_auth_mutations.ResendActivationEmail.Field()
    send_password_reset_email = graphql_auth_mutations.SendPasswordResetEmail.Field()
    password_reset = graphql_auth_mutations.PasswordReset.Field()
    password_set = graphql_auth_mutations.PasswordSet.Field()
    password_change = graphql_auth_mutations.PasswordChange.Field()
    update_account = graphql_auth_mutations.UpdateAccount.Field()
    archive_account = graphql_auth_mutations.ArchiveAccount.Field()
    delete_account = graphql_auth_mutations.DeleteAccount.Field()
    send_secondary_email_activation = graphql_auth_mutations.SendSecondaryEmailActivation.Field()
    verify_secondary_email = graphql_auth_mutations.VerifySecondaryEmail.Field()
    swap_emails = graphql_auth_mutations.SwapEmails.Field()
    remove_secondary_email = graphql_auth_mutations.RemoveSecondaryEmail.Field()

    token_auth = graphql_auth_mutations.ObtainJSONWebToken.Field()
    verify_token = graphql_auth_mutations.VerifyToken.Field()
    refresh_token = graphql_auth_mutations.RefreshToken.Field()
    revoke_token = graphql_auth_mutations.RevokeToken.Field()


schema = graphene.Schema(query=Query, mutation=Mutation)
