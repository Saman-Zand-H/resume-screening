import contextlib

import graphene
from common.exceptions import GraphQLError, GraphQLErrorBadRequest
from common.mixins import (
    ArrayChoiceTypeMixin,
    CUDOutputTypeMixin,
    DocumentFilePermissionMixin,
    FilePermissionMixin,
)
from common.models import Job, Skill
from common.types import SkillType
from common.utils import fields_join
from notification.models import InAppNotification
from notification.senders import NotificationContext, send_notifications
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
from graphql_auth import mutations as graphql_auth_mutations
from graphql_auth.bases import SuccessErrorsOutput
from graphql_auth.constants import TokenAction
from graphql_auth.exceptions import EmailAlreadyInUseError
from graphql_auth.models import UserStatus
from graphql_auth.settings import graphql_auth_settings
from graphql_auth.shortcuts import get_user_by_email
from graphql_auth.utils import get_token, get_token_payload
from graphql_jwt.decorators import (
    login_required,
    on_token_auth_resolve,
    refresh_expiration,
)

from account.utils import is_env
from django.contrib.auth.signals import user_logged_in
from django.db import transaction
from django.db.models import F
from django.db.models.functions import Lower
from django.db.utils import IntegrityError
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.translation import gettext as _

from .accesses import (
    JobPositionContainer,
    OrganizationMembershipContainer,
    OrganizationProfileContainer,
)
from .choices import DefaultRoles
from .forms import PasswordLessRegisterForm
from .mixins import (
    CRUDWithoutIDMutationMixin,
    DocumentCheckPermissionsMixin,
    DocumentCUDFieldMixin,
    DocumentCUDMixin,
    DocumentUpdateMutationMixin,
    EmailVerificationMixin,
    MutationAccessRequiredMixin,
    UpdateStatusMixin,
)
from .models import (
    CanadaVisa,
    CertificateAndLicense,
    CertificateAndLicenseOfflineVerificationMethod,
    CommunicateOrganizationMethod,
    Contact,
    DocumentAbstract,
    Education,
    EmployerLetterMethod,
    JobPositionAssignment,
    JobPositionInterview,
    LanguageCertificate,
    LanguageCertificateValue,
    Organization,
    OrganizationInvitation,
    OrganizationJobPosition,
    OrganizationMembership,
    Profile,
    ReferenceCheckEmployer,
    Referral,
    ReferralUser,
    Resume,
    Role,
    SupportTicket,
    User,
    WorkExperience,
)
from .tasks import (
    get_certificate_text,
    send_email_async,
    set_user_resume_json,
    set_user_skills,
    user_task_runner,
)
from .types import (
    CertificateAndLicenseNode,
    EducationNode,
    LanguageCertificateNode,
    OrganizationJobPositionNode,
    ProfileType,
    UserNode,
    WorkExperienceNode,
)
from .views import GoogleOAuth2View, LinkedInOAuth2View


class OrganizationInviteMutation(MutationAccessRequiredMixin, DocumentCUDMixin, DjangoCreateMutation):
    accesses = [OrganizationMembershipContainer.INVITOR, OrganizationMembershipContainer.ADMIN]

    class Meta:
        model = OrganizationInvitation
        fields = (
            OrganizationInvitation.organization.field.name,
            OrganizationInvitation.email.field.name,
            OrganizationInvitation.role.field.name,
        )

    @classmethod
    def get_access_object(cls, *args, **kwargs):
        if not (
            organization := Organization.objects.filter(
                pk=kwargs.get("input", {}).get(OrganizationInvitation.organization.field.name)
            ).first()
        ):
            raise GraphQLErrorBadRequest(_("Organization not found."))

        return organization

    @classmethod
    def before_create_obj(cls, info, input, obj):
        user = info.context.user
        obj.created_by = user
        OrganizationInvitation.objects.filter(email=obj.email, organization=obj.organization).delete()
        cls.full_clean(obj)

    @classmethod
    def after_mutate(cls, root, info, input, obj: OrganizationInvitation, return_data):
        template_name = "email/invitation.html"
        context = {"email": obj.email, "organization": obj.organization, "role": obj.role.title, "token": obj.token}
        content = render_to_string(template_name, context)
        send_email_async.delay(
            recipient_list=[obj.email],
            from_email=None,
            subject=_("Welcome to CPJ - You have been invited!"),
            content=content,
        )
        return super().after_mutate(root, info, input, obj, return_data)


def referral_registration(user, referral_code):
    if not referral_code:
        return
    referral = Referral.objects.filter(code__iexact=referral_code).first()
    if referral:
        ReferralUser.objects.create(user=user, referral=referral)


EMAIL_CALLBACK_URL_VARIABLE = "email_callback_url"
EMAIL_RECEIVER_NAME_VARIABLE = "email_receiver_name"
TEMPLATE_CONTEXT_VARIABLE = "template_context"


def set_template_context_variable(context, key, value):
    _template_context = getattr(context, TEMPLATE_CONTEXT_VARIABLE, {})
    _template_context[key] = value
    setattr(context, TEMPLATE_CONTEXT_VARIABLE, _template_context)


class EmailCallbackUrlMixin:
    @classmethod
    def mutate(cls, *args, **kwargs):
        set_template_context_variable(
            args[1].context,
            EMAIL_CALLBACK_URL_VARIABLE,
            kwargs.get(EMAIL_CALLBACK_URL_VARIABLE),
        )
        return super().mutate(*args, **kwargs)

    @classmethod
    def Field(cls, *args, **kwargs):
        cls._required_args += [EMAIL_CALLBACK_URL_VARIABLE]
        return super().Field(*args, **kwargs)


class RegisterBase(EmailCallbackUrlMixin, graphql_auth_mutations.Register):
    form = PasswordLessRegisterForm

    @classmethod
    @transaction.atomic
    def mutate(cls, *args, **kwargs):
        email = kwargs.get(User.EMAIL_FIELD)
        set_template_context_variable(
            args[1].context,
            EMAIL_RECEIVER_NAME_VARIABLE,
            kwargs.get(cls.EMAIL_RECEIVER_NAME),
        )
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
        cls.after_mutate(*args, **kwargs)
        return result

    @classmethod
    def after_mutate(cls, *args, **kwargs):
        pass


class UserRegister(RegisterBase):
    _args = graphql_auth_mutations.Register._args + [
        "referral_code",
        OrganizationInvitation.token.field.name,
    ]

    EMAIL_RECEIVER_NAME = User.first_name.field.name

    @classmethod
    def after_mutate(cls, *args, **kwargs):
        referral_registration(
            User.objects.get(**{User.EMAIL_FIELD: kwargs.get(User.EMAIL_FIELD)}), kwargs.pop("referral_code", None)
        )
        if organization_invitation_token := kwargs.pop(OrganizationInvitation.token.field.name, None):
            organization_invitation = OrganizationInvitation.objects.filter(token=organization_invitation_token).first()
            if not organization_invitation:
                raise GraphQLErrorBadRequest(_("Organization invitation token is invalid."))

            if organization_invitation.is_expired:
                raise GraphQLErrorBadRequest(_("Organization invitation token is expired."))

            user = User.objects.get(**{User.EMAIL_FIELD: kwargs.get(User.EMAIL_FIELD)})
            try:
                OrganizationMembership.objects.create(
                    **{
                        OrganizationMembership.user.field.name: user,
                        OrganizationMembership.organization.field.name: organization_invitation.organization,
                        OrganizationMembership.role.field.name: organization_invitation.role,
                        OrganizationMembership.invited_by.field.name: organization_invitation.created_by,
                    }
                )
            except IntegrityError:
                raise GraphQLErrorBadRequest(_("User has already membership in an organization."))
            organization_invitation.delete()


class RegisterOrganization(RegisterBase):
    _required_args = [User.EMAIL_FIELD, Organization.name.field.name, "website"]

    EMAIL_RECEIVER_NAME = Organization.name.field.name

    @classmethod
    def after_mutate(cls, *args, **kwargs):
        if not (role := Role.objects.filter(**{Role.slug.field.name: DefaultRoles.OWNER}).first()):
            raise GraphQLError(_("Owner role not found."))

        user = User.objects.get(**{User.EMAIL_FIELD: kwargs.get(User.EMAIL_FIELD)})

        organization_name = kwargs.get(Organization.name.field.name)
        organization = Organization.objects.create(
            **{
                Organization.name.field.name: organization_name,
                Organization.user.field.name: user,
            }
        )
        Contact.objects.create(
            contactable=organization.contactable,
            type=Contact.Type.WEBSITE.value,
            value=kwargs.get("website"),
        )

        try:
            OrganizationMembership.objects.create(
                **{
                    OrganizationMembership.user.field.name: user,
                    OrganizationMembership.organization.field.name: organization,
                    OrganizationMembership.role.field.name: role,
                    OrganizationMembership.invited_by.field.name: user,
                }
            )
        except IntegrityError:
            raise GraphQLErrorBadRequest(_("User has already membership in an organization."))


class VerifyAccount(graphql_auth_mutations.VerifyAccount):
    token = graphene.String(description="The token required to set password after registration with password_reset")

    @classmethod
    def mutate(cls, *args, **kwargs):
        response = super().mutate(*args, **kwargs)
        if response.success:
            payload = get_token_payload(kwargs.get("token"), TokenAction.ACTIVATION, None)
            user = User.objects.get(**payload)
            response.token = get_token(user, TokenAction.PASSWORD_RESET)
            send_email_async.delay(
                [user.email],
                None,
                subject=_("Welcome to CPJ - Your Journey to Career Excellence Starts Here!"),
                content=render_to_string("email/welcome.html", {"user": user}),
            )

            in_app_notification = InAppNotification(
                user=user,
                title=_("Welcome to CPJ"),
                body=_("Your Journey to Career Excellence Starts Here!"),
            )
            notification = NotificationContext(notification=in_app_notification)
            send_notifications(notification)

        return response


class ResendActivationEmail(EmailCallbackUrlMixin, graphql_auth_mutations.ResendActivationEmail):
    pass


class SendPasswordResetEmail(EmailCallbackUrlMixin, graphql_auth_mutations.SendPasswordResetEmail):
    @classmethod
    def mutate(cls, *args, **kwargs):
        user = get_user_by_email(kwargs.get("email"))
        set_template_context_variable(
            args[1].context,
            EMAIL_RECEIVER_NAME_VARIABLE,
            user.first_name if user.first_name else user.email,
        )
        return super().mutate(*args, **kwargs)


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


class ObtainJSONWebToken(graphql_auth_mutations.ObtainJSONWebToken):
    @classmethod
    def mutate(cls, root, info, **input):
        output = super().mutate(root, info, **input)
        if output.success:
            user: User = output.user
            user_logged_in.send(sender=user.__class__, request=None, user=user)
        return output


class OrganizationUpdateMutation(
    MutationAccessRequiredMixin,
    FilePermissionMixin,
    DocumentCUDMixin,
    DjangoPatchMutation,
):
    accesses = [OrganizationProfileContainer.COMPANY_EDITOR, OrganizationProfileContainer.ADMIN]

    @classmethod
    def get_access_object(cls, *args, **kwargs):
        if not (organization := Organization.objects.filter(pk=kwargs.get("id")).first()):
            raise GraphQLErrorBadRequest(_("Organization not found."))

        return organization

    class Meta:
        model = Organization
        fields = (
            Organization.name.field.name,
            Organization.logo.field.name,
            Organization.short_name.field.name,
            Organization.national_number.field.name,
            Organization.type.field.name,
            Organization.business_type.field.name,
            Organization.industry.field.name,
            Organization.established_at.field.name,
            Organization.size.field.name,
            Organization.about.field.name,
        )

    @classmethod
    def check_permissions(cls, root, info, input, id, obj) -> None:
        if obj.status != Organization.Status.DRAFTED.value:
            raise PermissionError("Not permitted to modify this record.")

        return super().check_permissions(root, info, input, id, obj)

    @classmethod
    def update_obj(cls, *args, **kwargs):
        obj = super().update_obj(*args, **kwargs)
        cls.full_clean(obj)
        return obj


class SetContactableMixin:
    @classmethod
    def __init_subclass_with_meta__(cls, *args, **kwargs):
        kwargs.update(
            {
                "model": Contact,
                "fields": [Contact.type.field.name, Contact.value.field.name],
                "login_required": True,
            }
        )
        return super().__init_subclass_with_meta__(*args, **kwargs)

    @classmethod
    def before_mutate(cls, root, info, input):
        if len(input) > len(set([c.get(Contact.type.field.name) for c in input])):
            raise GraphQLErrorBadRequest("Contact types must be unique.")
        return super().before_mutate(root, info, input)

    @classmethod
    def before_create_obj(cls, info, input, obj: Contact):
        contactable = cls.get_contactable_object(info, input)
        with contextlib.suppress(Contact.DoesNotExist):
            obj.pk = Contact.objects.get(contactable=contactable, type=obj.type).pk
        obj.contactable = contactable
        obj.full_clean(validate_unique=False)

    @classmethod
    def after_mutate(cls, root, info, input, created_objs, return_data):
        contactable = cls.get_contactable_object(info, input)
        Contact.objects.filter(contactable=contactable).exclude(pk__in=[obj.pk for obj in created_objs]).delete()

    @classmethod
    def get_contactable_object(cls, info, input):
        raise NotImplementedError


class SetOrganizationContactsMutation(MutationAccessRequiredMixin, SetContactableMixin, DjangoBatchCreateMutation):
    accesses = [OrganizationProfileContainer.COMPANY_EDITOR, OrganizationProfileContainer.ADMIN]

    class Meta:
        custom_fields = {"organization_id": graphene.ID(required=True)}
        type_name = "SetOrganizationContactableInput"

    @classmethod
    def get_access_object(cls, *args, **kwargs):
        input = kwargs.get("input")
        organization_id = input[0].get("organization_id") if type(input) is list else input.get("organization_id")
        if not (organization := Organization.objects.filter(pk=organization_id).first()):
            raise GraphQLErrorBadRequest(_("Organization not found."))

        return organization

    @classmethod
    def get_contactable_object(cls, info, input):
        organization_id = input[0].get("organization_id") if type(input) is list else input.get("organization_id")
        organization = Organization.objects.filter(pk=organization_id).first()
        if not organization:
            raise GraphQLErrorBadRequest("Organization not found.")
        return organization.contactable


USER_MUTATION_FIELDS = get_input_fields_for_model(
    User,
    fields=(
        fields := (
            User.first_name.field.name,
            User.last_name.field.name,
        )
    ),
    optional_fields=fields,
    exclude=tuple(),
)


class UserUpdateMutation(
    CUDOutputTypeMixin, FilePermissionMixin, ArrayChoiceTypeMixin, CRUDWithoutIDMutationMixin, DjangoUpdateMutation
):
    output_type = ProfileType

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
            Profile.gender.field.name,
            Profile.birth_date.field.name,
            Profile.interested_jobs.field.name,
            Profile.city.field.name,
            Profile.native_language.field.name,
            Profile.fluent_languages.field.name,
            Profile.job_cities.field.name,
            Profile.job_type.field.name,
            Profile.job_location_type.field.name,
            Profile.allow_notifications.field.name,
            Profile.accept_terms_and_conditions.field.name,
            Profile.skills.field.name,
        )
        custom_fields = USER_MUTATION_FIELDS

    @classmethod
    def get_object_id(cls, context):
        return context["info"].context.user.profile.pk

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
        user: User = info.context.user
        profile = user.profile

        if interested_jobs := set(input.get(Profile.interested_jobs.field.name, set())):
            if Job.objects.filter(id__in=interested_jobs, require_appearance_data=True).exists():
                if any(input.get(item, object()) in (None, "") for item in Profile.get_appearance_related_fields()):
                    raise GraphQLErrorBadRequest(_("Appearance related data cannot be unset."))

                if not (profile.has_appearance_related_data):
                    if any(input.get(item) is None for item in Profile.get_appearance_related_fields()):
                        raise GraphQLErrorBadRequest(_("Appearance related data is required."))
        if (skills := input.get(Profile.skills.field.name)) and profile.skills.filter(pk__in=skills).count() != len(
            skills
        ):
            raise GraphQLErrorBadRequest(_("Skills must be selected from the list."))

        return super().validate(*args, **kwargs)


class UserSkillInput(graphene.InputObjectType):
    skills = graphene.List(graphene.String, required=True)


class UserSetSkillsMutation(graphene.Mutation):
    class Arguments:
        input = UserSkillInput(required=True)

    user = graphene.Field(UserNode)

    @login_required
    @staticmethod
    def mutate(root, info, input):
        user: User = info.context.user
        profile = user.profile
        profile.raw_skills = (skills := input.get("skills"))
        profile.save(update_fields=[Profile.raw_skills.field.name])

        if skills:
            user_task_runner(set_user_skills, task_user_id=user.id, user_id=user.id)
        else:
            profile.skills.clear()

        return UserSetSkillsMutation(user=user)


class SetUserContactsMutation(SetContactableMixin, DjangoBatchCreateMutation):
    @classmethod
    def get_contactable_object(cls, info, input):
        return info.context.user.profile.contactable


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
    verification_new_status = DocumentAbstract.Status.SUBMITTED

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
        obj.status = cls.verification_new_status.value
        obj.save(update_fields=[DocumentAbstract.status.field.name])

        if isinstance((verification_method := obj.get_verification_method()), EmailVerificationMixin):
            verification_method.send_verification()

        return super().after_mutate(root, info, id, input, obj, return_data)


EDUCATION_MUTATION_FIELDS = (
    Education.field.field.name,
    Education.degree.field.name,
    Education.university.field.name,
    Education.city.field.name,
    Education.start.field.name,
    Education.end.field.name,
)


class EducationCreateMutation(CUDOutputTypeMixin, DocumentCreateMutationBase):
    output_type = EducationNode

    class Meta:
        model = Education
        fields = EDUCATION_MUTATION_FIELDS


class EducationUpdateMutation(CUDOutputTypeMixin, DocumentPatchMutationBase):
    output_type = EducationNode

    class Meta:
        model = Education
        fields = EDUCATION_MUTATION_FIELDS


class EducationDeleteMutation(DocumentCheckPermissionsMixin, DjangoDeleteMutation):
    class Meta:
        model = Education


class EducationSetVerificationMethodMutation(
    CUDOutputTypeMixin, DocumentFilePermissionMixin, DocumentSetVerificationMethodMutation
):
    output_type = EducationNode

    class Meta:
        model = Education


class EducationUpdateStatusMutation(CUDOutputTypeMixin, UpdateStatusMixin):
    output_type = EducationNode

    class Meta:
        model = Education


WORK_EXPERIENCE_MUTATION_FIELDS = (
    WorkExperience.job_title.field.name,
    WorkExperience.grade.field.name,
    WorkExperience.start.field.name,
    WorkExperience.end.field.name,
    WorkExperience.organization.field.name,
    WorkExperience.city.field.name,
    WorkExperience.industry.field.name,
    WorkExperience.skills.field.name,
)


class WorkExperienceCreateMutation(CUDOutputTypeMixin, DocumentCreateMutationBase):
    output_type = WorkExperienceNode

    class Meta:
        model = WorkExperience
        fields = WORK_EXPERIENCE_MUTATION_FIELDS


class WorkExperienceUpdateMutation(CUDOutputTypeMixin, DocumentPatchMutationBase):
    output_type = WorkExperienceNode

    class Meta:
        model = WorkExperience
        fields = WORK_EXPERIENCE_MUTATION_FIELDS


class WorkExperienceDeleteMutation(DocumentCheckPermissionsMixin, DjangoDeleteMutation):
    class Meta:
        model = WorkExperience


class WorkExperienceSetVerificationMethodMutation(
    CUDOutputTypeMixin, DocumentFilePermissionMixin, DocumentSetVerificationMethodMutation
):
    output_type = WorkExperienceNode

    @classmethod
    def after_mutate(cls, root, info, id, input, obj, return_data):
        return super().after_mutate(root, info, id, input, obj, return_data)

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
            raise GraphQLErrorBadRequest(
                "Employer letter method must be associated with a work experience verification."
            )

        return super().validate(root, info, input, id, obj)


class WorkExperienceUpdateStatusMutation(CUDOutputTypeMixin, UpdateStatusMixin):
    output_type = WorkExperienceNode

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


class LanguageCertificateCreateMutation(CUDOutputTypeMixin, DocumentCreateMutationBase):
    output_type = LanguageCertificateNode

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


class LanguageCertificateUpdateMutation(CUDOutputTypeMixin, DocumentPatchMutationBase):
    output_type = LanguageCertificateNode

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
    CUDOutputTypeMixin, DocumentFilePermissionMixin, DocumentSetVerificationMethodMutation
):
    output_type = LanguageCertificateNode
    verification_new_status = DocumentAbstract.Status.SELF_VERIFIED

    class Meta:
        model = LanguageCertificate


class LanguageCertificateUpdateStatusMutation(CUDOutputTypeMixin, UpdateStatusMixin):
    output_type = LanguageCertificateNode

    class Meta:
        model = LanguageCertificate


CERTIFICATE_AND_LICENSE_MUTATION_FIELDS = (
    CertificateAndLicense.title.field.name,
    CertificateAndLicense.certifier.field.name,
    CertificateAndLicense.issued_at.field.name,
    CertificateAndLicense.expired_at.field.name,
)


class CertificateAndLicenseCreateMutation(CUDOutputTypeMixin, DocumentCreateMutationBase):
    output_type = CertificateAndLicenseNode

    class Meta:
        model = CertificateAndLicense
        fields = CERTIFICATE_AND_LICENSE_MUTATION_FIELDS


class CertificateAndLicenseUpdateMutation(CUDOutputTypeMixin, DocumentPatchMutationBase):
    output_type = CertificateAndLicenseNode

    class Meta:
        model = CertificateAndLicense
        fields = CERTIFICATE_AND_LICENSE_MUTATION_FIELDS


class CertificateAndLicenseDeleteMutation(DocumentCheckPermissionsMixin, DjangoDeleteMutation):
    class Meta:
        model = CertificateAndLicense


class CertificateAndLicenseSetVerificationMethodMutation(
    CUDOutputTypeMixin, DocumentFilePermissionMixin, DocumentSetVerificationMethodMutation
):
    output_type = CertificateAndLicenseNode
    verification_new_status = DocumentAbstract.Status.SELF_VERIFIED

    class Meta:
        model = CertificateAndLicense

    @classmethod
    def after_mutate(cls, root, info, id, input, obj, return_data):
        super().after_mutate(root, info, id, input, obj, return_data)

        if not isinstance(
            obj.get_verification_method(),
            CertificateAndLicenseOfflineVerificationMethod,
        ):
            return

        user_task_runner(
            get_certificate_text,
            task_user_id=info.context.user.id,
            certificate_id=obj.id,
        )


class CertificateAndLicenseUpdateStatusMutation(CUDOutputTypeMixin, UpdateStatusMixin):
    output_type = CertificateAndLicenseNode

    class Meta:
        model = CertificateAndLicense


class UploadCompanyCertificateMethodInput(graphene.InputObjectType):
    organization_certificate_file_id = graphene.ID(required=True)


class CommunicateOrganizationMethodInput(graphene.InputObjectType):
    phonenumber = graphene.String(required=True)
    email = graphene.String(required=False)


class OrganizationVerificationMethodInput(graphene.InputObjectType):
    dnstxtrecordmethod = graphene.String()
    uploadfiletowebsitemethod = graphene.String()
    uploadcompanycertificatemethod = graphene.Field(UploadCompanyCertificateMethodInput)
    communicateorganizationmethod = graphene.Field(CommunicateOrganizationMethodInput)


class BaseOrganizationVerifierMutation(MutationAccessRequiredMixin):
    accesses = [OrganizationProfileContainer.VERIFIER, OrganizationProfileContainer.ADMIN]

    @classmethod
    def get_access_object(cls, *args, **kwargs):
        if not (organization := Organization.objects.filter(pk=kwargs.get("id")).first()):
            raise GraphQLErrorBadRequest(_("Organization not found."))

        return organization


class OrganizationSetVerificationMethodMutation(BaseOrganizationVerifierMutation, graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        input = OrganizationVerificationMethodInput(required=True)

    success = graphene.Boolean()
    output = GenericScalar()

    @classmethod
    @transaction.atomic
    @login_required
    def mutate(cls, root, info, id, input):
        method, input_data = next(((key, value) for key, value in input.items() if value is not None), (None, None))

        if method is None:
            raise GraphQLErrorBadRequest(_("No verification method provided."))

        organization = cls.get_access_object(id=id)
        if organization.status in Organization.get_verified_statuses():
            raise GraphQLErrorBadRequest(_("Organization verification method is already set."))

        if verification_method := organization.get_verification_method():
            verification_method.delete()

        method_model = {m.get_related_name(): m for m in Organization.get_method_models()}[method]
        method_instance = method_model.objects.create(organization=organization, **(input_data or {}))
        return cls(success=True, output=method_instance.get_output())


class OrganizationCommunicationMethodVerify(BaseOrganizationVerifierMutation, graphene.Mutation):
    class Arguments:
        organization = graphene.ID(required=True)
        otp = graphene.String(required=True, description="OTP sent to the phone number.")

    success = graphene.Boolean()

    @classmethod
    def get_access_object(cls, *args, **kwargs):
        if not (organization := Organization.objects.filter(pk=kwargs.get("organization")).first()):
            raise GraphQLErrorBadRequest(_("Organization not found."))

        return organization

    @classmethod
    @login_required
    def mutate(cls, root, info, organization, otp):
        organization = cls.get_access_object(organization=organization)

        try:
            model = organization.communicateorganizationmethod
        except CommunicateOrganizationMethod.DoesNotExist:
            raise GraphQLErrorBadRequest(_("Cannot verify OTP."))

        result = model.verify_otp(otp)
        return cls(success=result)


ORGANIZATION_JOB_POSITION_FIELDS = [
    OrganizationJobPosition.title.field.name,
    OrganizationJobPosition.vaccancy.field.name,
    OrganizationJobPosition.start_at.field.name,
    OrganizationJobPosition.validity_date.field.name,
    OrganizationJobPosition.description.field.name,
    OrganizationJobPosition.skills.field.name,
    OrganizationJobPosition.fields.field.name,
    OrganizationJobPosition.degrees.field.name,
    OrganizationJobPosition.work_experience_years_range.field.name,
    OrganizationJobPosition.languages.field.name,
    OrganizationJobPosition.native_languages.field.name,
    OrganizationJobPosition.age_range.field.name,
    OrganizationJobPosition.required_documents.field.name,
    OrganizationJobPosition.performance_expectation.field.name,
    OrganizationJobPosition.contract_type.field.name,
    OrganizationJobPosition.location_type.field.name,
    OrganizationJobPosition.salary_range.field.name,
    OrganizationJobPosition.payment_term.field.name,
    OrganizationJobPosition.working_start_at.field.name,
    OrganizationJobPosition.working_end_at.field.name,
    OrganizationJobPosition.benefits.field.name,
    OrganizationJobPosition.other_benefits.field.name,
    OrganizationJobPosition.days_off.field.name,
    OrganizationJobPosition.job_restrictions.field.name,
    OrganizationJobPosition.employer_questions.field.name,
    OrganizationJobPosition.city.field.name,
]


class OrganizationJobPositionCreateMutation(
    CUDOutputTypeMixin, MutationAccessRequiredMixin, ArrayChoiceTypeMixin, DjangoCreateMutation
):
    output_type = OrganizationJobPositionNode
    accesses = [JobPositionContainer.CREATEOR, JobPositionContainer.ADMIN]

    @classmethod
    def get_access_object(cls, *args, **kwargs):
        if not (
            organization := Organization.objects.filter(
                pk=kwargs.get("input", {}).get(OrganizationJobPosition.organization.field.name)
            ).first()
        ):
            raise GraphQLErrorBadRequest(_("Organization not found."))

        return organization

    class Meta:
        model = OrganizationJobPosition
        login_required = True
        fields = ORGANIZATION_JOB_POSITION_FIELDS + [
            OrganizationJobPosition.organization.field.name,
        ]

    @classmethod
    def before_create_obj(cls, info, input, obj):
        obj.full_clean()


class OrganizationJobPositionUpdateMutation(
    CUDOutputTypeMixin, MutationAccessRequiredMixin, ArrayChoiceTypeMixin, DjangoPatchMutation
):
    output_type = OrganizationJobPositionNode
    accesses = [JobPositionContainer.EDITOR, JobPositionContainer.ADMIN]

    @classmethod
    def get_access_object(cls, *args, **kwargs):
        if not (
            organization := Organization.objects.filter(
                **{fields_join(OrganizationJobPosition.organization.field.related_query_name(), "pk"): kwargs.get("id")}
            ).first()
        ):
            raise GraphQLErrorBadRequest(_("Organization not found."))

        return organization

    class Meta:
        model = OrganizationJobPosition
        login_required = True
        fields = ORGANIZATION_JOB_POSITION_FIELDS

    @classmethod
    def validate(cls, root, info, input, id, obj):
        if obj.status != OrganizationJobPosition.Status.DRAFTED.value:
            raise GraphQLErrorBadRequest(f"Cannot modify job position with status {obj.status}.")
        return super().validate(root, info, input, id, obj)

    @classmethod
    def update_obj(cls, *args, **kwargs):
        obj = super().update_obj(*args, **kwargs)
        obj.full_clean()
        return obj


class OrganizationJobPositionStatusUpdateMutation(CUDOutputTypeMixin, MutationAccessRequiredMixin, DjangoPatchMutation):
    output_type = OrganizationJobPositionNode
    accesses = [JobPositionContainer.STATUS_CHANGER, JobPositionContainer.ADMIN]

    @classmethod
    def get_access_object(cls, *args, **kwargs):
        if not (
            organization := Organization.objects.filter(
                **{fields_join(OrganizationJobPosition.organization.field.related_query_name(), "pk"): kwargs.get("id")}
            ).first()
        ):
            raise GraphQLErrorBadRequest(_("Organization not found."))

        return organization

    class Meta:
        model = OrganizationJobPosition
        login_required = True
        fields = [OrganizationJobPosition._status.field.name]
        required_fields = [OrganizationJobPosition._status.field.name]
        type_name = "OrganizationJobPositionStatusUpdateInput"

    @classmethod
    @transaction.atomic
    def mutate(cls, root, info, input, id):
        status = input.get(OrganizationJobPosition._status.field.name)
        if not (obj := OrganizationJobPosition.objects.get(pk=id)):
            raise GraphQLErrorBadRequest(_("Job position not found."))

        obj.change_status(status)
        return cls(**{cls._meta.return_field_name: obj})


class JobPositionAssignmentStatusUpdateMutation(MutationAccessRequiredMixin, ArrayChoiceTypeMixin, DjangoPatchMutation):
    accesses = [JobPositionContainer.STATUS_CHANGER, JobPositionContainer.ADMIN]

    @classmethod
    def get_access_object(cls, *args, **kwargs):
        if not (
            organization := Organization.objects.filter(
                **{
                    fields_join(
                        OrganizationJobPosition.organization.field.related_query_name(),
                        JobPositionAssignment.job_position.field.related_query_name(),
                        "pk",
                    ): kwargs.get("id")
                }
            ).first()
        ):
            raise GraphQLErrorBadRequest(_("Organization not found."))

        return organization

    class Meta:
        model = JobPositionAssignment
        login_required = True
        fields = [JobPositionAssignment.status.field.name]
        required_fields = [JobPositionAssignment.status.field.name]
        custom_fields = {
            JobPositionInterview.interview_date.field.name: graphene.DateTime(),
            JobPositionInterview.result_date.field.name: graphene.DateTime(),
        }
        type_name = "JobPositionAssignmentStatusUpdateInput"

    @classmethod
    @transaction.atomic
    def mutate(cls, root, info, input, id):
        status = input.get(JobPositionAssignment.status.field.name)
        if not (obj := JobPositionAssignment.objects.get(pk=id)):
            raise GraphQLErrorBadRequest(_("Job position assignment not found."))

        interview_date = input.get(JobPositionInterview.interview_date.field.name)
        result_date = input.get(JobPositionInterview.result_date.field.name)

        obj.change_status(status, interview_date=interview_date, result_date=result_date)
        return cls(**{cls._meta.return_field_name: obj})


class CreateOrganizationSkillMutation(MutationAccessRequiredMixin, graphene.Mutation):
    accesses = [JobPositionContainer.SKILL_CREATOR, JobPositionContainer.ADMIN]

    class Arguments:
        organization = graphene.ID(required=True)
        skills = graphene.List(graphene.String, required=True)

    skills = graphene.List(SkillType)

    @classmethod
    def get_access_object(cls, *args, **kwargs):
        if not (organization := Organization.objects.filter(pk=kwargs.get("organization")).first()):
            raise GraphQLErrorBadRequest(_("Organization not found."))
        return organization

    @classmethod
    @login_required
    def mutate(cls, root, info, organization, skills):
        normalized_titles = {skill.strip().lower() for skill in skills if skill.strip()}
        existing_skills = Skill.objects.annotate(title_lower=Lower(F("title"))).filter(
            title_lower__in=normalized_titles
        )
        existing_titles = set(existing_skills.values_list("title_lower", flat=True))
        new_titles = normalized_titles - existing_titles
        new_skills = Skill.objects.bulk_create(
            [Skill(title=title.title(), insert_type=Skill.InsertType.ORGANIZATION) for title in new_titles]
        )
        all_skills = list(existing_skills) + new_skills
        return cls(skills=set(all_skills))


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
    set_contacts = SetUserContactsMutation.Field()
    set_skills = UserSetSkillsMutation.Field()
    upload_resume = ResumeCreateMutation.Field()

    if is_env(Environment.LOCAL, Environment.DEVELOPMENT):
        delete = UserDeleteMutation.Field()


class OrganizationMutation(graphene.ObjectType):
    register = RegisterOrganization.Field()
    invite = OrganizationInviteMutation.Field()
    update = OrganizationUpdateMutation.Field()
    set_contacts = SetOrganizationContactsMutation.Field()
    create_skills = CreateOrganizationSkillMutation.Field()
    set_verification_method = OrganizationSetVerificationMethodMutation.Field()
    verify_communication_method = OrganizationCommunicationMethodVerify.Field()
    create_job_position = OrganizationJobPositionCreateMutation.Field()
    update_job_position = OrganizationJobPositionUpdateMutation.Field()
    update_job_position_status = OrganizationJobPositionStatusUpdateMutation.Field()
    update_job_position_assignment_status = JobPositionAssignmentStatusUpdateMutation.Field()


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
    register = UserRegister.Field()
    verify = VerifyAccount.Field()
    resend_activation_email = ResendActivationEmail.Field()
    send_password_reset_email = SendPasswordResetEmail.Field()
    password_reset = graphql_auth_mutations.PasswordReset.Field()
    token_auth = ObtainJSONWebToken.Field()
    refresh_token = RefreshToken.Field()
    google_auth = GoogleAuth.Field()
    linkedin_auth = LinkedInAuth.Field()
    profile = graphene.Field(ProfileMutation)
    organization = graphene.Field(OrganizationMutation)
    education = graphene.Field(EducationMutation)
    work_experience = graphene.Field(WorkExperienceMutation)
    language_certificate = graphene.Field(LanguageCertificateMutation)
    certificate_and_license = graphene.Field(CertificateAndLicenseMutation)
    canada_visa = graphene.Field(CanadaVisaMutation)
    support_ticket = graphene.Field(SupportTicketMutation)

    def resolve_profile(self, *args, **kwargs):
        return ProfileMutation()

    def resolve_organization(self, *args, **kwargs):
        return OrganizationMutation()

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


class ErrMutation(graphene.Mutation):
    class Arguments:
        message = graphene.String(required=True)

    result = graphene.String()

    def mutate(self, info, message):
        raise GraphQLErrorBadRequest(_(message))
        return ErrMutation(result="Error")


class Mutation(graphene.ObjectType):
    error = ErrMutation.Field()
    account = graphene.Field(AccountMutation, required=True)

    def resolve_account(self, *args, **kwargs):
        return AccountMutation()
