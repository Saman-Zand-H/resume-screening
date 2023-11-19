import contextlib

import graphene
from graphene.types.generic import GenericScalar
from graphene_django_cud.mutations import (
    DjangoBatchCreateMutation,
    DjangoCreateMutation,
    DjangoDeleteMutation,
    DjangoPatchMutation,
    DjangoUpdateMutation,
)
from graphene_django_cud.mutations.create import get_input_fields_for_model
from graphql import GraphQLError
from graphql_auth import mutations as graphql_auth_mutations
from graphql_auth.bases import SuccessErrorsOutput
from graphql_auth.constants import TokenAction
from graphql_auth.exceptions import EmailAlreadyInUseError
from graphql_auth.models import UserStatus
from graphql_auth.settings import graphql_auth_settings
from graphql_auth.utils import get_token, get_token_payload
from graphql_jwt.decorators import on_token_auth_resolve, refresh_expiration

from django.core.exceptions import ValidationError
from django.utils import timezone

from .forms import PasswordLessRegisterForm
from .mixins import (
    DocumentCheckPermissionsMixin,
    DocumentCUDFieldMixin,
    DocumentCUDMixin,
    DocumentUpdateMutationMixin,
    FullCleanMixin,
)
from .models import (
    Contact,
    DocumentAbstract,
    Education,
    LanguageCertificate,
    Profile,
    User,
    WorkExperience,
    ReferenceCheckEmployer,
    CertificateAndLicense,
)
from .views import GoogleOAuth2View, LinkedInOAuth2View


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


class RefreshToken(graphql_auth_mutations.RefreshToken):
    @classmethod
    def Field(cls, *args, **kwargs):
        field = super().Field(*args, **kwargs)
        del cls._meta.fields["refresh_token"]
        del cls._meta.fields["refresh_expires_in"]
        return field


class BaseSocialAuth(SuccessErrorsOutput, graphene.Mutation):
    class Arguments:
        code = graphene.String(required=True)

    token = graphene.String()
    refresh_token = graphene.String()
    refresh_expires_in = graphene.Int()
    payload = GenericScalar()

    @classmethod
    def setup(cls, root, info, **kwargs):
        return NotImplemented

    @classmethod
    @refresh_expiration
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


USER_MUTATION_FIELDS = get_input_fields_for_model(
    User,
    fields=(
        fields := (
            User.first_name.field.name,
            User.last_name.field.name,
            User.gender.field.name,
            User.birth_date.field.name,
        )
    ),
    optional_fields=fields,
    exclude=tuple(),
)


class UserUpdateMutation(DjangoCreateMutation):
    class Meta:
        model = Profile
        login_required = True
        exclude = (Profile.user.field.name,)
        custom_fields = USER_MUTATION_FIELDS

    @classmethod
    def before_create_obj(cls, info, input, obj):
        user = info.context.user

        user_fields = USER_MUTATION_FIELDS.keys()
        for user_field in user_fields:
            if (user_field_value := input.get(user_field)) is not None:
                setattr(user, user_field, getattr(user_field_value, "value", user_field_value))
        user.full_clean()
        user.save()

        profile, _ = Profile.objects.get_or_create(user=user)
        obj.pk = profile.pk
        obj.user = user

        try:
            obj.full_clean(validate_unique=False)
        except ValidationError as e:
            user_field, message = next(iter(e.message_dict.items()))
            raise GraphQLError(f"{user_field}: {message[0]}")


class SetContactsMutation(DjangoBatchCreateMutation):
    class Meta:
        model = Contact
        login_required = True
        fields = (
            Contact.type.field.name,
            Contact.value.field.name,
        )

    @classmethod
    def before_mutate(cls, root, info, input):
        if len(input) > len(set([c.get(Contact.type.field.name) for c in input])):
            raise GraphQLError("Contact types must be unique.")
        return super().before_mutate(root, info, input)

    @classmethod
    def before_create_obj(cls, info, input, obj):
        obj.user = info.context.user
        with contextlib.suppress(Contact.DoesNotExist):
            obj.pk = Contact.objects.get(user=obj.user, type=obj.type).pk
        try:
            obj.full_clean(validate_unique=False)
        except ValidationError as e:
            raise GraphQLError(next(iter(e.messages)))

    @classmethod
    def after_mutate(cls, root, info, input, created_objs, return_data):
        Contact.objects.filter(user=info.context.user).exclude(pk__in=[obj.pk for obj in created_objs]).delete()


class DocumentCreateMutationBase(DocumentCUDFieldMixin, DocumentCUDMixin, DjangoCreateMutation):
    class Meta:
        abstract = True

    @classmethod
    def before_create_obj(cls, info, input, obj):
        obj.user = info.context.user
        cls.full_clean(obj)


class DocumentPatchMutationBase(DocumentCUDFieldMixin, DocumentUpdateMutationMixin, DjangoPatchMutation):
    class Meta:
        abstract = True


class DocumentSetVerificationMethodMutation(DocumentUpdateMutationMixin, DjangoUpdateMutation):
    class Meta:
        abstract = True

    @classmethod
    def __init_subclass_with_meta__(cls, *args, **kwargs):
        model = kwargs.get("model")
        kwargs.update(
            {
                "type_name": f"Set{model.__name__}VerificationMethodInput",
                "fields": (*(m.get_related_name() for m in model.get_method_models()),),
                "one_to_one_extras": {
                    m.get_related_name(): {
                        "type": "auto",
                        "exclude_fields": (model.verified_at.field.name,),
                    }
                    for m in model.get_method_models()
                },
            }
        )
        return super().__init_subclass_with_meta__(*args, **kwargs)

    @classmethod
    def before_create_obj(cls, info, input, obj):
        cls.full_clean(obj)

    @classmethod
    def validate(cls, root, info, input, id, obj):
        models = obj.get_method_models()
        method_inputs_exist = [input.get(m.get_related_name()) is not None for m in models]

        if not any(method_inputs_exist):
            raise GraphQLError("At least one method must be provided.")

        if sum(method_inputs_exist) > 1:
            raise GraphQLError("Only one of the methods can be provided.")

        return super().validate(root, info, input, id, obj)

    @classmethod
    def after_mutate(cls, root, info, id, input, obj, return_data):
        obj.status = DocumentAbstract.Status.SUBMITTED.value
        obj.save(update_fields=[DocumentAbstract.status.field.name])
        return super().after_mutate(root, info, id, input, obj, return_data)


EDUCATION_MUTATION_FIELDS = (
    Education.field.field.name,
    Education.degree.field.name,
    Education.university.field.name,
    Education.start.field.name,
    Education.end.field.name,
)


class EducationCreateMutation(DocumentCreateMutationBase):
    class Meta:
        model = Education
        fields = EDUCATION_MUTATION_FIELDS


class EducationUpdateMutation(DocumentPatchMutationBase):
    class Meta:
        model = Education
        fields = EDUCATION_MUTATION_FIELDS


class EducationDeleteMutation(DocumentCheckPermissionsMixin, DjangoDeleteMutation):
    class Meta:
        model = Education


class EducationSetVerificationMethodMutation(DocumentSetVerificationMethodMutation):
    class Meta:
        model = Education


class EducationUpdateStatusMutation(DjangoPatchMutation):
    class Meta:
        model = Education
        login_required = True
        fields = (Education.status.field.name,)
        type_name = "PatchEducationStatusInput"


WORK_EXPERIENCE_MUTATION_FIELDS = (
    WorkExperience.job.field.name,
    WorkExperience.start.field.name,
    WorkExperience.end.field.name,
    WorkExperience.skills.field.name,
    WorkExperience.organization.field.name,
    WorkExperience.city.field.name,
)


class WorkExperienceCreateMutation(DocumentCreateMutationBase):
    class Meta:
        model = WorkExperience
        fields = WORK_EXPERIENCE_MUTATION_FIELDS


class WorkExperienceUpdateMutation(DocumentPatchMutationBase):
    class Meta:
        model = WorkExperience
        fields = WORK_EXPERIENCE_MUTATION_FIELDS


class WorkExperienceDeleteMutation(DocumentCheckPermissionsMixin, DjangoDeleteMutation):
    class Meta:
        model = WorkExperience


class WorkExperienceSetVerificationMethodMutation(DocumentSetVerificationMethodMutation):
    class Meta:
        model = WorkExperience


LANGUAGE_CERTIFICATE_MUTATION_FIELDS = (
    LanguageCertificate.language.field.name,
    LanguageCertificate.test.field.name,
    LanguageCertificate.issued_at.field.name,
    LanguageCertificate.expired_at.field.name,
    LanguageCertificate.listening_score.field.name,
    LanguageCertificate.reading_score.field.name,
    LanguageCertificate.writing_score.field.name,
    LanguageCertificate.speaking_score.field.name,
    LanguageCertificate.band_score.field.name,
)


class LanguageCertificateCreateMutation(FullCleanMixin, DjangoCreateMutation):
    class Meta:
        model = LanguageCertificate
        login_required = True
        fields = LANGUAGE_CERTIFICATE_MUTATION_FIELDS

    @classmethod
    def before_create_obj(cls, info, input, obj):
        obj.user = info.context.user


class LanguageCertificateUpdateMutation(FullCleanMixin, DocumentCheckPermissionsMixin, DjangoPatchMutation):
    class Meta:
        model = LanguageCertificate
        login_required = True
        fields = LANGUAGE_CERTIFICATE_MUTATION_FIELDS


class LanguageCertificateDeleteMutation(DocumentCheckPermissionsMixin, DjangoDeleteMutation):
    class Meta:
        model = LanguageCertificate
        login_required = True


CERTIFICATE_AND_LICENSE_MUTATION_FIELDS = (
    CertificateAndLicense.title.field.name,
    CertificateAndLicense.certifier.field.name,
    CertificateAndLicense.issued_at.field.name,
    CertificateAndLicense.expired_at.field.name,
)


class CertificateAndLicenseCreateMutation(FullCleanMixin, DjangoCreateMutation):
    class Meta:
        model = CertificateAndLicense
        login_required = True
        fields = CERTIFICATE_AND_LICENSE_MUTATION_FIELDS

    @classmethod
    def before_create_obj(cls, info, input, obj):
        obj.user = info.context.user


class ProfileMutation(graphene.ObjectType):
    update = UserUpdateMutation.Field()
    set_contacts = SetContactsMutation.Field()


class EducationMutation(graphene.ObjectType):
    create = EducationCreateMutation.Field()
    update = EducationUpdateMutation.Field()
    delete = EducationDeleteMutation.Field()
    update_status = EducationUpdateStatusMutation.Field()
    set_verification_method = EducationSetVerificationMethodMutation.Field()


class WorkExperienceMutation(graphene.ObjectType):
    create = WorkExperienceCreateMutation.Field()
    update = WorkExperienceUpdateMutation.Field()
    delete = WorkExperienceDeleteMutation.Field()
    set_verification_method = WorkExperienceSetVerificationMethodMutation.Field()


class LanguageCertificateMutation(graphene.ObjectType):
    create = LanguageCertificateCreateMutation.Field()
    update = LanguageCertificateUpdateMutation.Field()
    delete = LanguageCertificateDeleteMutation.Field()


class CertificateAndLicenseMutation(graphene.ObjectType):
    create = CertificateAndLicenseCreateMutation.Field()


class AccountMutation(graphene.ObjectType):
    register = Register.Field()
    verify = VerifyAccount.Field()
    resend_activation_email = graphql_auth_mutations.ResendActivationEmail.Field()
    send_password_reset_email = graphql_auth_mutations.SendPasswordResetEmail.Field()
    password_reset = graphql_auth_mutations.PasswordReset.Field()
    password_change = graphql_auth_mutations.PasswordChange.Field()
    token_auth = graphql_auth_mutations.ObtainJSONWebToken.Field()
    verify_token = graphql_auth_mutations.VerifyToken.Field()
    refresh_token = RefreshToken.Field()
    revoke_token = graphql_auth_mutations.RevokeToken.Field()
    google_auth = GoogleAuth.Field()
    linkedin_auth = LinkedInAuth.Field()
    profile = graphene.Field(ProfileMutation)
    education = graphene.Field(EducationMutation)
    work_experience = graphene.Field(WorkExperienceMutation)
    language_certificate = graphene.Field(LanguageCertificateMutation)
    certificate_and_license = graphene.Field(CertificateAndLicenseMutation)

    def resolve_profile(self, *args, **kwargs):
        return ProfileMutation()

    def resolve_education(self, *args, **kwargs):
        return EducationMutation()

    def resolve_work_experience(self, *args, **kwargs):
        return WorkExperienceMutation()

    def resolve_language_certificate(self, *args, **kwargs):
        return LanguageCertificateMutation()

    def resolve_certificate_and_license(self, *args, **kwargs):
        return CertificateAndLicenseMutation()


class Mutation(graphene.ObjectType):
    account = graphene.Field(AccountMutation, required=True)

    def resolve_account(self, *args, **kwargs):
        return AccountMutation()
