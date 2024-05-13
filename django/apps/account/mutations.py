import contextlib

import graphene
from account.utils import is_env
from common.exceptions import GraphQLErrorBadRequest
from common.mixins import (
    ArrayChoiceTypeMixin,
    DocumentFilePermissionMixin,
    FilePermissionMixin,
)
from common.models import Job
from config.settings.constants import Environment
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
from graphql_jwt.decorators import (
    login_required,
    on_token_auth_resolve,
    refresh_expiration,
)

from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext as _

from .forms import PasswordLessRegisterForm
from .mixins import (
    CRUDWithoutIDMutationMixin,
    DocumentCheckPermissionsMixin,
    DocumentCUDFieldMixin,
    DocumentCUDMixin,
    DocumentUpdateMutationMixin,
    UpdateStatusMixin,
)
from .models import (
    CanadaVisa,
    CertificateAndLicense,
    Contact,
    DocumentAbstract,
    Education,
    EmployerLetterMethod,
    LanguageCertificate,
    LanguageCertificateValue,
    Profile,
    ReferenceCheckEmployer,
    Referral,
    ReferralUser,
    Resume,
    SupportTicket,
    User,
    WorkExperience,
)
from .tasks import set_user_resume_json, set_user_skills, user_task_runner
from .types.account import UserSkillType
from .views import GoogleOAuth2View, LinkedInOAuth2View


def referral_registration(user, referral_code):
    if not referral_code:
        return
    referral = Referral.objects.filter(code__iexact=referral_code).first()
    if referral:
        ReferralUser.objects.create(user=user, referral=referral)


class Register(graphql_auth_mutations.Register):
    form = PasswordLessRegisterForm
    _args = graphql_auth_mutations.Register._args + [
        "referral_code",
    ]

    @classmethod
    @transaction.atomic
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

        result = super().mutate(*args, **kwargs)
        if not result.success:
            return result

        referral_registration(User.objects.get(**{User.EMAIL_FIELD: email}), kwargs.pop("referral_code", None))

        return result


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
        referral_code = graphene.String()

    token = graphene.String()
    refresh_token = graphene.String()
    refresh_expires_in = graphene.Int()
    payload = GenericScalar()

    @classmethod
    def setup(cls, root, info, **kwargs):
        return NotImplementedError

    @classmethod
    @refresh_expiration
    @transaction.atomic
    def mutate(cls, root, info, **kwargs):
        payload = cls.setup(root, info, **kwargs)
        data = payload.get("data")
        view = payload.get("view")

        serializer = view.serializer_class(data=data, context={"view": view, "request": info.context})
        auth = serializer.validate(data)
        user = auth.get("user")
        user.status.verified = True
        user.username = user.email
        user.status.save(update_fields=["verified"])
        user.save(update_fields=["username"])
        on_token_auth_resolve((info.context, user, cls))

        if serializer.is_new_user:
            referral_registration(user, kwargs.get("referral_code"))

        cls.success = True
        cls.errors = None
        return cls


class GoogleAuth(BaseSocialAuth):
    @classmethod
    def setup(cls, root, info, code, **kwargs):
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


class UserUpdateMutation(FilePermissionMixin, ArrayChoiceTypeMixin, CRUDWithoutIDMutationMixin, DjangoUpdateMutation):
    class Meta:
        model = Profile
        login_required = True
        fields = (
            Profile.height.field.name,
            Profile.weight.field.name,
            Profile.skin_color.field.name,
            Profile.hair_color.field.name,
            Profile.eye_color.field.name,
            Profile.avatar.field.name,
            Profile.full_body_image.field.name,
            Profile.employment_status.field.name,
            Profile.interested_jobs.field.name,
            Profile.city.field.name,
            Profile.native_language.field.name,
            Profile.fluent_languages.field.name,
            Profile.job_cities.field.name,
            Profile.job_type.field.name,
            Profile.job_location_type.field.name,
        )
        custom_fields = USER_MUTATION_FIELDS

    @classmethod
    def get_object_id(cls, context):
        info = context.get("info")
        profile = Profile.objects.get_or_create(user=info.context.user)[0]
        return profile.pk

    @classmethod
    def before_save(cls, root, info, input, id, obj):
        user = info.context.user

        user_fields = USER_MUTATION_FIELDS.keys()
        for user_field in user_fields:
            if (user_field_value := input.get(user_field)) is not None:
                setattr(user, user_field, getattr(user_field_value, "value", user_field_value))
        user.full_clean()
        user.save()

        obj.full_clean()

    @classmethod
    def validate(cls, *args, **kwargs):
        info = args[1]
        input = args[2]
        user = info.context.user

        if interested_jobs := set(input.get(Profile.interested_jobs.field.name, set())):
            available_jobs = map(str, set(user.available_jobs.values_list("id", flat=True)))
            if not interested_jobs.issubset(available_jobs):
                raise GraphQLErrorBadRequest(_("Interested jobs must be in available jobs."))

            if Job.objects.filter(id__in=interested_jobs, require_appearance_data=True).exists():
                if any(input.get(item, object()) in (None, "") for item in Profile.get_appearance_related_fields()):
                    raise GraphQLErrorBadRequest(_("Appearance related data cannot be unset."))
                if not ((profile := user.get_profile()) and profile.has_appearance_related_data):
                    if any(input.get(item) is None for item in Profile.get_appearance_related_fields()):
                        raise GraphQLErrorBadRequest(_("Appearance related data is required."))

        return super().validate(*args, **kwargs)


class UserSkillInput(graphene.InputObjectType):
    skills = graphene.List(graphene.String, required=True)


class UserSetSkillsMutation(graphene.Mutation):
    class Arguments:
        input = UserSkillInput(required=True)

    user = graphene.Field(UserSkillType)

    @login_required
    @staticmethod
    def mutate(root, info, input):
        user = info.context.user
        skills = input.get("skills")
        user.raw_skills = skills
        user.save(update_fields=[User.raw_skills.field.name])

        user = (updated_user := set_user_skills(user_id=user.pk)) and updated_user or user
        return UserSetSkillsMutation(user=user)


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
            raise GraphQLErrorBadRequest("Contact types must be unique.")
        return super().before_mutate(root, info, input)

    @classmethod
    def before_create_obj(cls, info, input, obj):
        obj.user = info.context.user
        with contextlib.suppress(Contact.DoesNotExist):
            obj.pk = Contact.objects.get(user=obj.user, type=obj.type).pk
        obj.full_clean(validate_unique=False)

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
        method_extras = kwargs.pop("method_extras", {})
        kwargs.update(
            {
                "type_name": f"Set{model.__name__}VerificationMethodInput",
                "fields": (*(m.get_related_name() for m in model.get_method_models()),),
                "one_to_one_extras": {
                    m.get_related_name(): {
                        "type": "auto",
                        "exclude_fields": (model.verified_at.field.name,),
                        **method_extras.get(m, {}),
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
            raise GraphQLErrorBadRequest("At least one method must be provided.")

        if sum(method_inputs_exist) > 1:
            raise GraphQLErrorBadRequest("Only one of the methods can be provided.")

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
    Education.city.field.name,
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


class EducationSetVerificationMethodMutation(DocumentFilePermissionMixin, DocumentSetVerificationMethodMutation):
    class Meta:
        model = Education


class EducationUpdateStatusMutation(UpdateStatusMixin):
    class Meta:
        model = Education


WORK_EXPERIENCE_MUTATION_FIELDS = (
    WorkExperience.job_title.field.name,
    WorkExperience.grade.field.name,
    WorkExperience.start.field.name,
    WorkExperience.end.field.name,
    WorkExperience.organization.field.name,
    WorkExperience.city.field.name,
    WorkExperience.skills.field.name,
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


class WorkExperienceSetVerificationMethodMutation(DocumentFilePermissionMixin, DocumentSetVerificationMethodMutation):
    class Meta:
        model = WorkExperience
        method_extras = {
            EmployerLetterMethod: {
                "type": "WorkExperienceEmployerLetterMethodInput",
                "many_to_one_extras": {
                    ReferenceCheckEmployer.work_experience_verification.field.related_query_name(): {
                        "exact": {"type": "auto"},
                    },
                },
            }
        }

    @classmethod
    def validate(cls, root, info, input, id, obj):
        employer_letter_method = input.get(EmployerLetterMethod.get_related_name())

        if employer_letter_method and not employer_letter_method.get(
            ReferenceCheckEmployer.work_experience_verification.field.related_query_name()
        ):
            raise GraphQLError("Employer letter method must be associated with a work experience verification.")

        return super().validate(root, info, input, id, obj)


class WorkExperienceUpdateStatusMutation(UpdateStatusMixin):
    class Meta:
        model = WorkExperience


LANGUAGE_CERTIFICATE_MUTATION_FIELDS = (
    LanguageCertificate.language.field.name,
    LanguageCertificate.test.field.name,
    LanguageCertificate.issued_at.field.name,
    LanguageCertificate.expired_at.field.name,
)


def validate_language_certificate_skills(test, values):
    test_skills = test.skills
    skills = [value.get(LanguageCertificateValue.skill.field.name) for value in values]

    if not test_skills.exists():
        raise GraphQLErrorBadRequest(_("Test has no skills."))

    if test_skills.count() != test_skills.filter(pk__in=set(skills)).count():
        raise GraphQLErrorBadRequest(_("All skills must be provided."))


class LanguageCertificateCreateMutation(DocumentCreateMutationBase):
    class Meta:
        model = LanguageCertificate
        fields = LANGUAGE_CERTIFICATE_MUTATION_FIELDS
        many_to_one_extras = {
            LanguageCertificateValue.language_certificate.field.related_query_name(): {
                "exact": {
                    "type": "auto",
                }
            }
        }

    @classmethod
    def validate(cls, root, info, input):
        if not input.get(LanguageCertificateValue.language_certificate.field.related_query_name()):
            raise GraphQLErrorBadRequest(_("Language certificate value must be provided."))

        return super().validate(root, info, input)

    @classmethod
    def before_create_obj(cls, info, input, obj):
        super().before_create_obj(info, input, obj)

        if isinstance(obj, LanguageCertificate):
            obj.user = info.context.user
            values = input.get(LanguageCertificateValue.language_certificate.field.related_query_name())
            validate_language_certificate_skills(obj.test, values)


class LanguageCertificateUpdateMutation(DocumentPatchMutationBase):
    class Meta:
        model = LanguageCertificate
        fields = LANGUAGE_CERTIFICATE_MUTATION_FIELDS
        many_to_one_extras = {
            LanguageCertificateValue.language_certificate.field.related_query_name(): {
                "exact": {
                    "type": "auto",
                }
            }
        }

    @classmethod
    def validate(cls, root, info, input, id, obj):
        if (f := LanguageCertificateValue.language_certificate.field.related_query_name()) in input and not input[f]:
            raise GraphQLErrorBadRequest(_("Language certificate value must be provided."))

        return super().validate(root, info, input, id, obj)

    @classmethod
    def before_create_obj(cls, info, input, obj):
        obj.full_clean()

    @classmethod
    def before_save(cls, root, info, input, id, obj):
        values = input.get(LanguageCertificateValue.language_certificate.field.related_query_name())
        if values is None:
            values = [{LanguageCertificateValue.skill.field.name: value.skill.pk} for value in obj.values.all()]

        validate_language_certificate_skills(obj.test, values)

        return super().before_save(root, info, input, id, obj)


class LanguageCertificateDeleteMutation(DocumentCheckPermissionsMixin, DjangoDeleteMutation):
    class Meta:
        model = LanguageCertificate


class LanguageCertificateSetVerificationMethodMutation(
    DocumentFilePermissionMixin, DocumentSetVerificationMethodMutation
):
    class Meta:
        model = LanguageCertificate


class LanguageCertificateUpdateStatusMutation(UpdateStatusMixin):
    class Meta:
        model = LanguageCertificate


CERTIFICATE_AND_LICENSE_MUTATION_FIELDS = (
    CertificateAndLicense.title.field.name,
    CertificateAndLicense.certifier.field.name,
    CertificateAndLicense.issued_at.field.name,
    CertificateAndLicense.expired_at.field.name,
)


class CertificateAndLicenseCreateMutation(DocumentCreateMutationBase):
    class Meta:
        model = CertificateAndLicense
        fields = CERTIFICATE_AND_LICENSE_MUTATION_FIELDS


class CertificateAndLicenseUpdateMutation(DocumentPatchMutationBase):
    class Meta:
        model = CertificateAndLicense
        fields = CERTIFICATE_AND_LICENSE_MUTATION_FIELDS


class CertificateAndLicenseDeleteMutation(DocumentCheckPermissionsMixin, DjangoDeleteMutation):
    class Meta:
        model = CertificateAndLicense


class CertificateAndLicenseSetVerificationMethodMutation(
    DocumentFilePermissionMixin, DocumentSetVerificationMethodMutation
):
    class Meta:
        model = CertificateAndLicense


class CertificateAndLicenseUpdateStatusMutation(UpdateStatusMixin):
    class Meta:
        model = CertificateAndLicense


class CanadaVisaCreateMutation(FilePermissionMixin, DocumentCUDMixin, DjangoCreateMutation):
    class Meta:
        model = CanadaVisa
        exclude = ("user",)

    @classmethod
    def before_create_obj(cls, info, input, obj):
        obj.user = info.context.user
        cls.full_clean(obj)


class SupportTicketCreateMutation(DocumentCUDMixin, DjangoCreateMutation):
    class Meta:
        model = SupportTicket
        fields = (
            SupportTicket.title.field.name,
            SupportTicket.description.field.name,
            SupportTicket.priority.field.name,
            SupportTicket.category.field.name,
            SupportTicket.contact_method.field.name,
            SupportTicket.contact_value.field.name,
        )

    @classmethod
    def before_create_obj(cls, info, input, obj):
        obj.user = info.context.user
        cls.full_clean(obj)


class ResumeCreateMutation(FilePermissionMixin, DocumentCUDMixin, CRUDWithoutIDMutationMixin, DjangoUpdateMutation):
    class Meta:
        model = Resume
        fields = (Resume.file.field.name,)

    @classmethod
    def get_object_id(cls, context):
        info = context.get("info")
        file = context.get("input").get(Resume.file.field.name)
        resume = Resume.objects.get_or_create(
            user=info.context.user,
            defaults={"file": Resume.file.field.related_model.objects.get(pk=file)},
        )[0]
        return resume.pk

    @classmethod
    def before_create_obj(cls, info, input, obj):
        obj.user = info.context.user
        cls.full_clean(obj)

    @classmethod
    def after_mutate(cls, root, info, id, input, obj, return_data):
        user_task_runner(set_user_resume_json, obj.user.id, user_id=obj.user_id)

        return super().after_mutate(root, info, id, input, obj, return_data)


class UserDeleteMutation(graphene.Mutation):
    class Arguments:
        email = graphene.String(required=True)

    deleted_objects = graphene.Int()

    @staticmethod
    def mutate(root, info, email):
        user = User.objects.get(email=email)
        return UserDeleteMutation(deleted_objects=user.delete()[0])


class ProfileMutation(graphene.ObjectType):
    update = UserUpdateMutation.Field()
    set_contacts = SetContactsMutation.Field()
    set_skills = UserSetSkillsMutation.Field()
    upload_resume = ResumeCreateMutation.Field()

    if is_env(Environment.LOCAL) or is_env(Environment.DEVELOPMENT):
        delete = UserDeleteMutation.Field()


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
    update_status = WorkExperienceUpdateStatusMutation.Field()
    set_verification_method = WorkExperienceSetVerificationMethodMutation.Field()


class LanguageCertificateMutation(graphene.ObjectType):
    create = LanguageCertificateCreateMutation.Field()
    update = LanguageCertificateUpdateMutation.Field()
    delete = LanguageCertificateDeleteMutation.Field()
    update_status = LanguageCertificateUpdateStatusMutation.Field()
    set_verification_method = LanguageCertificateSetVerificationMethodMutation.Field()


class CertificateAndLicenseMutation(graphene.ObjectType):
    create = CertificateAndLicenseCreateMutation.Field()
    update = CertificateAndLicenseUpdateMutation.Field()
    delete = CertificateAndLicenseDeleteMutation.Field()
    update_status = CertificateAndLicenseUpdateStatusMutation.Field()
    set_verification_method = CertificateAndLicenseSetVerificationMethodMutation.Field()


class CanadaVisaMutation(graphene.ObjectType):
    create = CanadaVisaCreateMutation.Field()


class SupportTicketMutation(graphene.ObjectType):
    create = SupportTicketCreateMutation.Field()


class AccountMutation(graphene.ObjectType):
    register = Register.Field()
    verify = VerifyAccount.Field()
    resend_activation_email = graphql_auth_mutations.ResendActivationEmail.Field()
    send_password_reset_email = graphql_auth_mutations.SendPasswordResetEmail.Field()
    password_reset = graphql_auth_mutations.PasswordReset.Field()
    token_auth = graphql_auth_mutations.ObtainJSONWebToken.Field()
    refresh_token = RefreshToken.Field()
    google_auth = GoogleAuth.Field()
    linkedin_auth = LinkedInAuth.Field()
    profile = graphene.Field(ProfileMutation)
    education = graphene.Field(EducationMutation)
    work_experience = graphene.Field(WorkExperienceMutation)
    language_certificate = graphene.Field(LanguageCertificateMutation)
    certificate_and_license = graphene.Field(CertificateAndLicenseMutation)
    canada_visa = graphene.Field(CanadaVisaMutation)
    support_ticket = graphene.Field(SupportTicketMutation)

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

    def resolve_canada_visa(self, *args, **kwargs):
        return CanadaVisaMutation()

    def resolve_support_ticket(self, *args, **kwargs):
        return SupportTicketMutation()


class Mutation(graphene.ObjectType):
    account = graphene.Field(AccountMutation, required=True)

    def resolve_account(self, *args, **kwargs):
        return AccountMutation()
