import graphene
from graphene_django_cud.mutations import (
    DjangoCreateMutation,
    DjangoDeleteMutation,
    DjangoPatchMutation,
    DjangoUpdateMutation,
)
from graphql import GraphQLError
from graphql_auth import mutations as graphql_auth_mutations
from graphql_auth.bases import SuccessErrorsOutput
from graphql_auth.constants import TokenAction
from graphql_auth.exceptions import EmailAlreadyInUseError
from graphql_auth.models import UserStatus
from graphql_auth.settings import graphql_auth_settings
from graphql_auth.utils import get_token, get_token_payload
from graphql_jwt.decorators import on_token_auth_resolve

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone

from .forms import PasswordLessRegisterForm
from .models import Education, Profile
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


class ProfileUpdateMutation(DjangoUpdateMutation):
    class Meta:
        model = Profile
        login_required = True
        exclude = (Profile.user.field.name,)
        custom_fields = {
            User.first_name.field.name: graphene.String(),
            User.last_name.field.name: graphene.String(),
            User.gender.field.name: graphene.String(),
            User.birth_date.field.name: graphene.Date(),
            User.phone_number.field.name: graphene.String(),
        }

    @classmethod
    def mutate(cls, root, info, input, id):
        user = info.context.user
        if not user.is_authenticated:
            raise GraphQLError("You must be logged in to update your profile.")
        profile, _ = Profile.objects.get_or_create(user=user)

        user_fields = [
            User.first_name.field.name,
            User.last_name.field.name,
            User.gender.field.name,
            User.birth_date.field.name,
            User.phone_number.field.name,
        ]
        for field in user_fields:
            if field in input:
                setattr(user, field, input[field])
        user.save()

        return super().mutate(root, info, input, profile.id)


class EducationCreateMutation(DjangoCreateMutation):
    class Meta:
        model = Education
        login_required = True
        fields = (
            Education.field.field.name,
            Education.degree.field.name,
            Education.university.field.name,
            Education.start.field.name,
            Education.end.field.name,
            Education.method.field.name,
            *(m.get_related_name() for m in Education.get_method_models()),
        )

        one_to_one_extras = {m.get_related_name(): {"type": "auto"} for m in Education.get_method_models()}

    @classmethod
    def validate(cls, root, info, input):
        models = Education.get_method_models()
        method = input.get(Education.method.field.name)

        if method.value == Education.Method.SELF_VERIFICATION:
            for m in models:
                if input.get(m.get_related_name()):
                    raise GraphQLError("Self verification method can't have any method inputs.")
        else:
            method_inputs_exist = [input.get(m.get_related_name()) is not None for m in models]
            if not input.get((field_name := Education.get_method_choices().get(method.value).get_related_name())):
                raise GraphQLError(f"{field_name} method must be provided.")
            if sum(method_inputs_exist) > 1:
                raise GraphQLError("Only one of the methods can be provided.")

        return super().validate(root, info, input)

    @classmethod
    def before_create_obj(cls, info, input, obj):
        if isinstance(obj, Education):
            obj.user = info.context.user
        else:
            try:
                obj.full_clean()
            except ValidationError as e:
                raise GraphQLError(e.message_dict)


class EducationUpdateMutation(DjangoPatchMutation):
    class Meta:
        model = Education
        login_required = True
        exclude = (
            Education.user.field.name,
            Education.status.field.name,
            "educationverification_set",
            Education.created_at.field.name,
            Education.updated_at.field.name,
        )

    @classmethod
    def check_permissions(cls, root, info, input, id, obj):
        super().check_permissions(root, info, input, id, obj)
        user = info.context.user
        if obj.user != user:
            raise GraphQLError("You don't have permission to modify this education record.")
        if obj.status != Education.Status.DRAFT:
            raise GraphQLError("You can only modify education records with 'draft' status.")


class EducationDeleteMutation(DjangoDeleteMutation):
    class Meta:
        model = Education
        login_required = True

    @classmethod
    def check_permissions(cls, root, info, id, obj):
        super().check_permissions(root, info, id, obj)
        user = info.context.user
        if obj.user != user:
            raise GraphQLError("You don't have permission to modify this education record.")
        if obj.status != Education.Status.DRAFT:
            raise GraphQLError("You can only modify education records with 'draft' status.")


class ProfileMutation(graphene.ObjectType):
    update = ProfileUpdateMutation.Field()


class EducationMutation(graphene.ObjectType):
    create = EducationCreateMutation.Field()
    update = EducationUpdateMutation.Field()
    delete = EducationDeleteMutation.Field()


class AccountMutation(graphene.ObjectType):
    register = Register.Field()
    verify = VerifyAccount.Field()
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
    profile = graphene.Field(ProfileMutation)
    education = graphene.Field(EducationMutation)

    def resolve_profile(self, *args, **kwargs):
        return ProfileMutation()

    def resolve_education(self, *args, **kwargs):
        return EducationMutation()


class Mutation(graphene.ObjectType):
    account = graphene.Field(AccountMutation, required=True)

    def resolve_account(self, *args, **kwargs):
        return AccountMutation()
