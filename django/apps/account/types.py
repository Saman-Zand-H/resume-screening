import graphene
from graphene_django_optimizer import OptimizedDjangoObjectType as DjangoObjectType
from graphql_auth.queries import CountableConnection
from graphql_auth.queries import UserNode as BaseUserNode
from graphql_auth.settings import graphql_auth_settings

from .models import (
    CommunicationMethod,
    Contact,
    Education,
    IEEMethod,
    LanguageCertificate,
    CertificateAndLicense,
    Profile,
    User,
    WorkExperience,
    EmployerLetterMethod,
    PaystubsMethod,
    ReferenceCheckEmployer,
)


class ProfileType(DjangoObjectType):
    class Meta:
        model = Profile
        fields = (
            Profile.height.field.name,
            Profile.weight.field.name,
            Profile.skin_color.field.name,
            Profile.hair_color.field.name,
            Profile.eye_color.field.name,
            Profile.full_body_image.field.name,
            Profile.employment_status.field.name,
            Profile.interested_jobs.field.name,
            Profile.city.field.name,
        )


class ContactType(DjangoObjectType):
    class Meta:
        model = Contact
        fields = (
            Contact.id.field.name,
            Contact.type.field.name,
            Contact.value.field.name,
        )


class EducationMethodFieldTypes(graphene.ObjectType):
    method = graphene.String()
    field = graphene.String()


class EducationType(DjangoObjectType):
    class Meta:
        model = Education
        fields = (
            Education.id.field.name,
            Education.field.field.name,
            Education.degree.field.name,
            Education.university.field.name,
            Education.start.field.name,
            Education.end.field.name,
            Education.status.field.name,
            Education.created_at.field.name,
            Education.updated_at.field.name,
            *(m.get_related_name() for m in Education.get_method_models()),
        )

    @classmethod
    def get_queryset(cls, queryset, info):
        user = info.context.user
        if not user:
            return queryset.none()
        return super().get_queryset(queryset, info).filter(user=user)


class IEEMethodType(DjangoObjectType):
    class Meta:
        model = IEEMethod
        fields = (
            IEEMethod.id.field.name,
            IEEMethod.ices_document.field.name,
            IEEMethod.citizen_document.field.name,
            IEEMethod.evaluator.field.name,
        )


class CommunicationMethodType(DjangoObjectType):
    class Meta:
        model = CommunicationMethod
        fields = (
            CommunicationMethod.id.field.name,
            CommunicationMethod.email.field.name,
            CommunicationMethod.department.field.name,
            CommunicationMethod.person.field.name,
            CommunicationMethod.degree_file.field.name,
        )


class WorkExperienceType(DjangoObjectType):
    class Meta:
        model = WorkExperience
        fields = (
            WorkExperience.id.field.name,
            WorkExperience.job.field.name,
            WorkExperience.start.field.name,
            WorkExperience.end.field.name,
            WorkExperience.skills.field.name,
            WorkExperience.organization.field.name,
            WorkExperience.city.field.name,
            WorkExperience.status.field.name,
            WorkExperience.created_at.field.name,
            WorkExperience.updated_at.field.name,
            *(m.get_related_name() for m in WorkExperience.get_method_models()),
        )

    @classmethod
    def get_queryset(cls, queryset, info):
        user = info.context.user
        if not user:
            return queryset.none()
        return super().get_queryset(queryset, info).filter(user=user)


class EmployerLetterMethodType(DjangoObjectType):
    class Meta:
        model = EmployerLetterMethod
        fields = (
            EmployerLetterMethod.id.field.name,
            EmployerLetterMethod.employer_letter.field.name,
        )


class PaystubsMethodType(DjangoObjectType):
    class Meta:
        model = PaystubsMethod
        fields = (
            PaystubsMethod.id.field.name,
            PaystubsMethod.paystubs.field.name,
        )


class ReferenceCheckEmployerType(DjangoObjectType):
    class Meta:
        model = ReferenceCheckEmployer
        fields = (
            ReferenceCheckEmployer.id.field.name,
            ReferenceCheckEmployer.name.field.name,
            ReferenceCheckEmployer.email.field.name,
            ReferenceCheckEmployer.phone_number.field.name,
            ReferenceCheckEmployer.position.field.name,
        )


class LanguageCertificateType(DjangoObjectType):
    class Meta:
        model = LanguageCertificate
        fields = (
            LanguageCertificate.id.field.name,
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


class CertificateAndLicenseType(DjangoObjectType):
    class Meta:
        model = CertificateAndLicense
        fields = (
            CertificateAndLicense.id.field.name,
            CertificateAndLicense.title.field.name,
            CertificateAndLicense.certifier.field.name,
            CertificateAndLicense.issued_at.field.name,
            CertificateAndLicense.expired_at.field.name,
        )


class UserNode(BaseUserNode):
    class Meta:
        model = User
        filter_fields = graphql_auth_settings.USER_NODE_FILTER_FIELDS
        interfaces = (graphene.relay.Node,)
        connection_class = CountableConnection
        fields = (
            User.first_name.field.name,
            User.last_name.field.name,
            User.gender.field.name,
            User.email.field.name,
            User.birth_date.field.name,
            Profile.user.field.related_query_name(),
            Contact.user.field.related_query_name(),
            Education.user.field.related_query_name(),
            WorkExperience.user.field.related_query_name(),
            LanguageCertificate.user.field.related_query_name(),
        )
