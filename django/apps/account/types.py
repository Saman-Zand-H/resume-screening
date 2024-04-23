import graphene
from criteria.models import JobAssessment
from criteria.types import JobAssessmentFilterInput, JobAssessmentType
from graphene_django_optimizer import OptimizedDjangoObjectType as DjangoObjectType
from graphql_auth.queries import CountableConnection
from graphql_auth.queries import UserNode as BaseUserNode
from graphql_auth.settings import graphql_auth_settings

from .mixins import FilterQuerySetByUserMixin
from .models import (
    CanadaVisa,
    CertificateAndLicense,
    CommunicationMethod,
    Contact,
    Education,
    EmployerLetterMethod,
    IEEMethod,
    LanguageCertificate,
    LanguageCertificateValue,
    PaystubsMethod,
    Profile,
    ReferenceCheckEmployer,
    Referral,
    Resume,
    User,
    WorkExperience,
)


class ProfileType(DjangoObjectType):
    fluent_languages = graphene.List(graphene.String)

    class Meta:
        model = Profile
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
            Profile.credits.field.name,
            Profile.job_cities.field.name,
            Profile.job_type.field.name,
            Profile.job_location_type.field.name,
        )

    def resolve_fluent_languages(self, info):
        if self.fluent_languages:
            return [lang.upper() for lang in self.fluent_languages]
        return []


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


class EducationNode(FilterQuerySetByUserMixin, DjangoObjectType):
    class Meta:
        model = Education
        use_connection = True
        fields = (
            Education.id.field.name,
            Education.field.field.name,
            Education.degree.field.name,
            Education.university.field.name,
            Education.city.field.name,
            Education.start.field.name,
            Education.end.field.name,
            Education.status.field.name,
            Education.created_at.field.name,
            Education.updated_at.field.name,
            Education.allow_self_verification.field.name,
            *(m.get_related_name() for m in Education.get_method_models()),
        )


class IEEMethodType(DjangoObjectType):
    class Meta:
        model = IEEMethod
        fields = (
            IEEMethod.id.field.name,
            IEEMethod.education_evaluation_document.field.name,
            IEEMethod.evaluator.field.name,
        )


class CommunicationMethodType(DjangoObjectType):
    class Meta:
        model = CommunicationMethod
        fields = (
            CommunicationMethod.id.field.name,
            CommunicationMethod.website.field.name,
            CommunicationMethod.email.field.name,
            CommunicationMethod.department.field.name,
            CommunicationMethod.person.field.name,
            CommunicationMethod.degree_file.field.name,
        )


class WorkExperienceNode(FilterQuerySetByUserMixin, DjangoObjectType):
    class Meta:
        model = WorkExperience
        use_connection = True
        fields = (
            WorkExperience.id.field.name,
            WorkExperience.job.field.name,
            WorkExperience.grade.field.name,
            WorkExperience.start.field.name,
            WorkExperience.end.field.name,
            WorkExperience.organization.field.name,
            WorkExperience.city.field.name,
            WorkExperience.skills.field.name,
            WorkExperience.created_at.field.name,
            WorkExperience.updated_at.field.name,
            WorkExperience.status.field.name,
            WorkExperience.allow_self_verification.field.name,
            *(m.get_related_name() for m in WorkExperience.get_method_models()),
        )


class EmployerLetterMethodType(DjangoObjectType):
    class Meta:
        model = EmployerLetterMethod
        fields = (
            EmployerLetterMethod.id.field.name,
            EmployerLetterMethod.employer_letter.field.name,
            ReferenceCheckEmployer.work_experience_verification.field.related_query_name(),
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


class LanguageCertificateNode(FilterQuerySetByUserMixin, DjangoObjectType):
    class Meta:
        model = LanguageCertificate
        use_connection = True
        fields = (
            LanguageCertificate.id.field.name,
            LanguageCertificate.language.field.name,
            LanguageCertificate.test.field.name,
            LanguageCertificate.status.field.name,
            LanguageCertificate.issued_at.field.name,
            LanguageCertificate.expired_at.field.name,
            LanguageCertificate.allow_self_verification.field.name,
            LanguageCertificateValue.language_certificate.field.related_query_name(),
        )


class LanguageCertificateValueNode(DjangoObjectType):
    class Meta:
        model = LanguageCertificateValue
        use_connection = True
        fields = (
            LanguageCertificateValue.id.field.name,
            LanguageCertificateValue.skill.field.name,
            LanguageCertificateValue.value.field.name,
        )


class CertificateAndLicenseNode(FilterQuerySetByUserMixin, DjangoObjectType):
    class Meta:
        model = CertificateAndLicense
        use_connection = True
        fields = (
            CertificateAndLicense.id.field.name,
            CertificateAndLicense.title.field.name,
            CertificateAndLicense.certifier.field.name,
            CertificateAndLicense.issued_at.field.name,
            CertificateAndLicense.expired_at.field.name,
            CertificateAndLicense.status.field.name,
            CertificateAndLicense.allow_self_verification.field.name,
        )


class CanadaVisaNode(FilterQuerySetByUserMixin, DjangoObjectType):
    class Meta:
        model = CanadaVisa
        use_connection = True
        fields = (
            CanadaVisa.id.field.name,
            CanadaVisa.nationality.field.name,
            CanadaVisa.status.field.name,
            CanadaVisa.citizenship_document.field.name,
        )


class ResumeType(DjangoObjectType):
    class Meta:
        model = Resume
        fields = (Resume.file.field.name,)


class ReferralType(DjangoObjectType):
    class Meta:
        model = Referral
        fields = (Referral.code.field.name,)


class UserNode(BaseUserNode):
    educations = graphene.List(EducationNode)
    workexperiences = graphene.List(WorkExperienceNode)
    languagecertificates = graphene.List(LanguageCertificateNode)
    certificateandlicenses = graphene.List(CertificateAndLicenseNode)
    job_assessments = graphene.List(
        JobAssessmentType, filters=graphene.Argument(JobAssessmentFilterInput, required=False)
    )
    has_resume = graphene.Boolean(source=User.has_resume.fget.__name__)

    class Meta:
        model = User
        filter_fields = graphql_auth_settings.USER_NODE_FILTER_FIELDS
        use_connection = True
        connection_class = CountableConnection
        fields = (
            User.first_name.field.name,
            User.last_name.field.name,
            User.gender.field.name,
            User.email.field.name,
            User.birth_date.field.name,
            User.skills.field.name,
            User.available_jobs.field.name,
            Profile.user.field.related_query_name(),
            Contact.user.field.related_query_name(),
            CanadaVisa.user.field.related_query_name(),
            Referral.user.field.related_query_name(),
            Resume.user.field.related_query_name(),
        )

    def resolve_educations(self, info):
        return self.educations.all().order_by("-id")

    def resolve_workexperiences(self, info):
        return self.workexperiences.all().order_by("-id")

    def resolve_languagecertificates(self, info):
        return self.languagecertificates.all().order_by("-id")

    def resolve_certificateandlicenses(self, info):
        return self.certificateandlicenses.all().order_by("-id")

    def resolve_job_assessments(self, info, filters=None):
        qs = JobAssessment.objects.related_to_user(self)
        if filters:
            if filters.required is not None:
                qs = qs.filter_by_required(filters.required, self.profile.interested_jobs.all())
        return qs.order_by("-id")


class UserSkillType(DjangoObjectType):
    class Meta:
        model = User
        fields = (
            User.id.field.name,
            User.raw_skills.field.name,
        )
