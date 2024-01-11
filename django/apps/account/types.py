import graphene
from graphene_django_optimizer import OptimizedDjangoObjectType as DjangoObjectType
from graphql_auth.queries import CountableConnection
from graphql_auth.queries import UserNode as BaseUserNode
from graphql_auth.settings import graphql_auth_settings
from django.db.models import Q, Count

from .mixins import FilterQuerySetByUserMixin
from .models import (
    CertificateAndLicense,
    CommunicationMethod,
    Contact,
    Education,
    EmployerLetterMethod,
    IEEMethod,
    LanguageCertificate,
    PaystubsMethod,
    Profile,
    ReferenceCheckEmployer,
    User,
    WorkExperience,
    CanadaVisa,
    JobAssessmentResult,
)
from common.types import JobAssessmentJobNode
from common.models import JobAssessment


class JobAssessmentResultFilterInput(graphene.InputObjectType):
    created_at_start = graphene.Date()
    created_at_end = graphene.Date()
    updated_at_start = graphene.Date()
    updated_at_end = graphene.Date()


class JobAssessmentFilterInput(graphene.InputObjectType):
    required = graphene.Boolean()
    no_results = graphene.Boolean()


class JobAssessmentResultNode(FilterQuerySetByUserMixin, DjangoObjectType):
    class Meta:
        model = JobAssessmentResult
        interfaces = (graphene.relay.Node,)
        fields = (
            JobAssessmentResult.id.field.name,
            JobAssessmentResult.status.field.name,
            JobAssessmentResult.score.field.name,
            JobAssessmentResult.created_at.field.name,
            JobAssessmentResult.updated_at.field.name,
        )


class JobAssessmentNode(DjangoObjectType):
    jobs = graphene.List(JobAssessmentJobNode)
    results = graphene.List(
        JobAssessmentResultNode, filters=graphene.Argument(JobAssessmentResultFilterInput, required=False)
    )

    class Meta:
        model = JobAssessment
        interfaces = (graphene.relay.Node,)
        fields = (
            JobAssessment.id.field.name,
            JobAssessment.service_id.field.name,
            JobAssessment.title.field.name,
            JobAssessment.logo.field.name,
            JobAssessment.short_description.field.name,
            JobAssessment.description.field.name,
            JobAssessment.resumable.field.name,
        )

    def resolve_jobs(self, info):
        user = info.context.user
        return self.job_assessment_jobs.filter(job__in=user.profile.interested_jobs.values_list("pk", flat=True))

    def resolve_results(self, info, filters=None):
        user = info.context.user
        if not user:
            return []

        results = JobAssessmentResult.objects.filter(job_assessment=self, user=user).order_by("-id")

        if filters:
            if filters.created_at_start and filters.created_at_end:
                results = results.filter(created_at__range=[filters.created_at_start, filters.created_at_end])

            if filters.updated_at_start and filters.updated_at_end:
                results = results.filter(updated_at__range=[filters.updated_at_start, filters.updated_at_end])
        return results


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


class EducationNode(FilterQuerySetByUserMixin, DjangoObjectType):
    class Meta:
        model = Education
        interfaces = (graphene.relay.Node,)
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
            Education.allow_self_verification.field.name,
            *(m.get_related_name() for m in Education.get_method_models()),
        )


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


class WorkExperienceNode(FilterQuerySetByUserMixin, DjangoObjectType):
    class Meta:
        model = WorkExperience
        interfaces = (graphene.relay.Node,)
        fields = (
            WorkExperience.id.field.name,
            WorkExperience.job.field.name,
            WorkExperience.start.field.name,
            WorkExperience.end.field.name,
            WorkExperience.organization.field.name,
            WorkExperience.city.field.name,
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
        interfaces = (graphene.relay.Node,)
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
            LanguageCertificate.status.field.name,
            LanguageCertificate.allow_self_verification.field.name,
        )


class CertificateAndLicenseNode(FilterQuerySetByUserMixin, DjangoObjectType):
    class Meta:
        model = CertificateAndLicense
        interfaces = (graphene.relay.Node,)
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
        interfaces = (graphene.relay.Node,)
        fields = (
            CanadaVisa.id.field.name,
            CanadaVisa.nationality.field.name,
            CanadaVisa.status.field.name,
            CanadaVisa.citizenship_document.field.name,
        )


class UserNode(BaseUserNode):
    educations = graphene.List(EducationNode)
    workexperiences = graphene.List(WorkExperienceNode)
    languagecertificates = graphene.List(LanguageCertificateNode)
    certificateandlicenses = graphene.List(CertificateAndLicenseNode)
    job_assessments = graphene.List(
        JobAssessmentNode, filters=graphene.Argument(JobAssessmentFilterInput, required=False)
    )

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
            User.skills.field.name,
            User.available_jobs.field.name,
            Profile.user.field.related_query_name(),
            Contact.user.field.related_query_name(),
            CanadaVisa.user.field.related_query_name(),
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
        qs = JobAssessment.objects
        q_object = Q(related_jobs__in=self.profile.interested_jobs.all())

        if filters:
            if filters.required is True:
                q_object &= Q(job_assessment_jobs__required=True)
            elif filters.required is False:
                qs = qs.annotate(
                    required_job_assessments=Count("job_assessment_jobs", filter=Q(job_assessment_jobs__required=True))
                ).filter(required_job_assessments=0)
            if filters.no_results is not None:
                q_object &= Q(results__isnull=filters.no_results)

        return qs.filter(q_object).distinct().order_by("-id")


class UserSkillType(DjangoObjectType):
    class Meta:
        model = User
        fields = (
            User.id.field.name,
            User.raw_skills.field.name,
        )
