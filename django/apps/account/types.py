import contextlib

import graphene
from common.mixins import ArrayChoiceTypeMixin
from common.models import Job
from common.types import JobNode, JobBenefitType, SkillType, FieldType
from common.utils import fields_join
from criteria.models import JobAssessment
from criteria.types import JobAssessmentFilterInput, JobAssessmentType
from cv.models import GeneratedCV
from graphene_django.filter import DjangoFilterConnectionField
from graphene_django_optimizer import OptimizedDjangoObjectType as DjangoObjectType
from graphql_auth.queries import CountableConnection
from graphql_auth.queries import UserNode as BaseUserNode
from graphql_auth.settings import graphql_auth_settings

from django.contrib.contenttypes.models import ContentType
from django.db.models import Case, IntegerField, Q, QuerySet, Value, When, Count

from .accesses import (
    JobPositionContainer,
    OrganizationMembershipContainer,
)
from .mixins import FilterQuerySetByUserMixin, ObjectTypeAccessRequiredMixin
from .models import (
    Access,
    CanadaVisa,
    CertificateAndLicense,
    CommunicationMethod,
    Contact,
    Education,
    EmployerLetterMethod,
    IEEMethod,
    JobPositionAssignment,
    JobPositionAssignmentStatusHistory,
    JobPositionInterview,
    LanguageCertificate,
    LanguageCertificateValue,
    Organization,
    OrganizationInvitation,
    OrganizationJobPosition,
    OrganizationMembership,
    PaystubsMethod,
    Profile,
    ReferenceCheckEmployer,
    Referral,
    Resume,
    Role,
    SupportTicket,
    SupportTicketCategory,
    User,
    UserTask,
    WorkExperience,
)


class ContactType(DjangoObjectType):
    class Meta:
        model = Contact
        fields = (
            Contact.id.field.name,
            Contact.type.field.name,
            Contact.value.field.name,
        )


class JobSeekerEducationType(DjangoObjectType):
    class Meta:
        model = Education
        fields = (
            Education.id.field.name,
            Education.field.field.name,
            Education.degree.field.name,
            Education.university.field.name,
            Education.city.field.name,
            Education.start.field.name,
            Education.end.field.name,
            Education.status.field.name,
        )


class JobSeekerWorkExperienceType(DjangoObjectType):
    class Meta:
        model = WorkExperience
        fields = (
            WorkExperience.id.field.name,
            WorkExperience.job_title.field.name,
            WorkExperience.grade.field.name,
            WorkExperience.organization.field.name,
            WorkExperience.city.field.name,
            WorkExperience.start.field.name,
            WorkExperience.end.field.name,
            WorkExperience.status.field.name,
        )


class JobSeekerLanguageCertificateType(DjangoObjectType):
    class Meta:
        model = LanguageCertificate
        fields = (
            LanguageCertificate.id.field.name,
            LanguageCertificate.language.field.name,
            LanguageCertificate.test.field.name,
            LanguageCertificate.issued_at.field.name,
            LanguageCertificate.expired_at.field.name,
            LanguageCertificate.status.field.name,
        )


class JobSeekerCertificateAndLicenseType(DjangoObjectType):
    class Meta:
        model = CertificateAndLicense
        fields = (
            CertificateAndLicense.id.field.name,
            CertificateAndLicense.title.field.name,
            CertificateAndLicense.certifier.field.name,
            CertificateAndLicense.issued_at.field.name,
            CertificateAndLicense.expired_at.field.name,
            CertificateAndLicense.status.field.name,
        )


class JobSeekerProfileType(DjangoObjectType):
    contacts = graphene.List(ContactType)

    class Meta:
        model = Profile
        fields = (
            Profile.avatar.field.name,
            Profile.full_body_image.field.name,
            Profile.score.field.name,
            Profile.contactable.field.name,
        )

    def resolve_contacts(self, info):
        return self.contactable.contacts.all()


class JobSeekerType(DjangoObjectType):
    profile = graphene.Field(JobSeekerProfileType)
    educations = graphene.List(JobSeekerEducationType)
    workexperiences = graphene.List(JobSeekerWorkExperienceType)
    languagecertificates = graphene.List(JobSeekerLanguageCertificateType)
    certificateandlicenses = graphene.List(JobSeekerCertificateAndLicenseType)

    class Meta:
        model = User
        fields = (
            User.first_name.field.name,
            User.last_name.field.name,
            User.email.field.name,
            Resume.user.field.related_query_name(),
            GeneratedCV.user.field.related_query_name(),
        )

    def resolve_profile(self, info):
        return self.profile

    def resolve_educations(self, info):
        return self.educations.all().order_by("-id")

    def resolve_workexperiences(self, info):
        return self.workexperiences.all().order_by("-id")

    def resolve_languagecertificates(self, info):
        return self.languagecertificates.all().order_by("-id")

    def resolve_certificateandlicenses(self, info):
        return self.certificateandlicenses.all().order_by("-id")


class ProfileType(ArrayChoiceTypeMixin, DjangoObjectType):
    completion_percentage = graphene.Float(source=Profile.completion_percentage.fget.__name__)
    contacts = graphene.List(ContactType)
    available_jobs = DjangoFilterConnectionField(JobNode)

    class Meta:
        model = Profile
        fields = (
            Profile.height.field.name,
            Profile.weight.field.name,
            Profile.skin_color.field.name,
            Profile.hair_color.field.name,
            Profile.eye_color.field.name,
            Profile.avatar.field.name,
            Profile.gender.field.name,
            Profile.birth_date.field.name,
            Profile.skills.field.name,
            Profile.full_body_image.field.name,
            Profile.employment_status.field.name,
            Profile.interested_jobs.field.name,
            Profile.city.field.name,
            Profile.native_language.field.name,
            Profile.credits.field.name,
            Profile.job_cities.field.name,
            Profile.job_type.field.name,
            Profile.job_location_type.field.name,
            Profile.fluent_languages.field.name,
            Profile.scores.field.name,
            Profile.score.field.name,
            Profile.contactable.field.name,
            Profile.raw_skills.field.name,
            Profile.allow_notifications.field.name,
            Profile.accept_terms_and_conditions.field.name,
        )

    def resolve_contacts(self, info):
        return self.contactable.contacts.all()

    def resolve_available_jobs(self, info, **kwargs):
        return (
            JobNode.get_queryset(JobNode._meta.model.objects.all(), info)
            .annotate(
                _priority=Case(
                    When(id__in=self.available_jobs.values("pk"), then=Value(1)),
                    default=Value(2),
                    output_field=IntegerField(),
                )
            )
            .order_by("_priority", Job.order.field.name, Job.title.field.name)
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
            WorkExperience.job_title.field.name,
            WorkExperience.grade.field.name,
            WorkExperience.start.field.name,
            WorkExperience.end.field.name,
            WorkExperience.organization.field.name,
            WorkExperience.city.field.name,
            WorkExperience.industry.field.name,
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
            LanguageCertificate.status.field.name,
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


class SupportTicketCategoryNode(ArrayChoiceTypeMixin, DjangoObjectType):
    class Meta:
        model = SupportTicketCategory
        use_connection = True
        fields = (
            SupportTicketCategory.id.field.name,
            SupportTicketCategory.title.field.name,
            SupportTicketCategory.types.field.name,
        )
        filter_fields = {
            SupportTicketCategory.types.field.name: ["contains"],
        }


class SupportTicketType(DjangoObjectType):
    class Meta:
        model = SupportTicket
        fields = (
            SupportTicket.id.field.name,
            SupportTicket.ticket_id.field.name,
            SupportTicket.title.field.name,
            SupportTicket.description.field.name,
            SupportTicket.status.field.name,
            SupportTicket.priority.field.name,
            SupportTicket.category.field.name,
            SupportTicket.contact_method.field.name,
            SupportTicket.contact_value.field.name,
            SupportTicket.created.field.name,
            SupportTicket.modified.field.name,
        )


class OrganizationMembershipUserType(DjangoObjectType):
    class Meta:
        model = User
        fields = (
            User.id.field.name,
            User.first_name.field.name,
            User.last_name.field.name,
            User.email.field.name,
        )


class AccessType(DjangoObjectType):
    class Meta:
        model = Access
        fields = (
            Access.id.field.name,
            Access.slug.field.name,
            Access.title.field.name,
        )


class RoleType(DjangoObjectType):
    class Meta:
        model = Role
        fields = (
            Role.id.field.name,
            Role.title.field.name,
            Role.description.field.name,
            Role.accesses.field.name,
        )


class OrganizationMembershipType(ObjectTypeAccessRequiredMixin, DjangoObjectType):
    fields_access = {
        "__all__": OrganizationMembershipContainer.get_accesses(),
    }

    user = graphene.Field(OrganizationMembershipUserType, source=OrganizationMembership.user.field.name)
    accessed_roles = graphene.List(RoleType)

    def resolve_accessed_roles(self, info):
        return Role.objects.filter(
            (
                Q(managed_by_id=self.organization_id)
                & Q(managed_by_model=ContentType.objects.get_for_model(Organization))
            )
            | (Q(managed_by_id__isnull=True) & Q(managed_by_model__isnull=True)),
        ).distinct()

    @classmethod
    def get_access_object(cls, *args, **kwargs):
        membership: OrganizationMembership = cls.get_obj_from_args(args)
        if not membership:
            return None

        return membership.organization

    class Meta:
        model = OrganizationMembership
        fields = (OrganizationMembership.role.field.name, OrganizationMembership.organization.field.name)


class UserTaskType(DjangoObjectType):
    class Meta:
        model = UserTask
        fields = (
            UserTask.task_name.field.name,
            UserTask.status.field.name,
        )


class UserNode(BaseUserNode):
    profile = graphene.Field(ProfileType)
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
            User.email.field.name,
            CanadaVisa.user.field.related_query_name(),
            Referral.user.field.related_query_name(),
            Resume.user.field.related_query_name(),
            SupportTicket.user.field.related_query_name(),
            UserTask.user.field.related_query_name(),
            GeneratedCV.user.field.related_query_name(),
            OrganizationMembership.user.field.related_query_name(),
        )

    def resolve_profile(self, info):
        return self.profile

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


class OrganizationType(DjangoObjectType):
    has_financial_data = graphene.Boolean()

    class Meta:
        model = Organization
        fields = (
            Organization.id.field.name,
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
            Organization.status.field.name,
            OrganizationInvitation.organization.field.related_query_name(),
            OrganizationMembership.organization.field.related_query_name(),
        )

    def resolve_has_financial_data(self, info):
        return True


class OrganizationInvitationType(ObjectTypeAccessRequiredMixin, DjangoObjectType):
    fields_access = {
        "__all__": [
            OrganizationMembershipContainer.INVITOR,
            OrganizationMembershipContainer.ADMIN,
        ]
    }

    @classmethod
    def get_access_object(cls, *args, **kwargs):
        invitation: OrganizationInvitation = cls.get_obj_from_args(args)
        if not invitation:
            return None

        return invitation.organization

    class Meta:
        model = OrganizationInvitation
        fields = (
            OrganizationInvitation.id.field.name,
            OrganizationInvitation.email.field.name,
            OrganizationInvitation.organization.field.name,
            OrganizationInvitation.role.field.name,
            OrganizationInvitation.created_at.field.name,
            OrganizationInvitation.created_by.field.name,
        )

    @classmethod
    def get_node_by_token(cls, info, token):
        model = cls._meta.model
        with contextlib.suppress(model.DoesNotExist):
            return model.objects.get(token=token)


class JobPositionAssignmentStatusCountType(graphene.ObjectType):
    status = graphene.String()
    count = graphene.Int()


class OrganizationJobPositionReportType(graphene.ObjectType):
    assignment_status_counts = graphene.List(JobPositionAssignmentStatusCountType)

    def resolve_assignment_status_counts(self, info, **kwargs):
        status_counts = (
            JobPositionAssignment.objects.filter(job_position=self)
            .values(
                JobPositionAssignment.status.field.name,
            )
            .annotate(count=Count(JobPositionAssignment.status.field.name))
        )

        return [
            JobPositionAssignmentStatusCountType(status=item["status"], count=item["count"]) for item in status_counts
        ]


JobPositionStatusEnum = graphene.Enum("JobPositionStatusEnum", OrganizationJobPosition.Status.choices)


class OrganizationJobPositionNode(ObjectTypeAccessRequiredMixin, ArrayChoiceTypeMixin, DjangoObjectType):
    fields_access = {
        "__all__": JobPositionContainer.get_accesses(),
    }
    status = graphene.Field(JobPositionStatusEnum, description="The current status of the job position.")
    age_range = graphene.List(graphene.Int, description="The age range of the job position.")
    salary_range = graphene.List(graphene.Int, description="The salary range of the job position.")
    work_experience_years_range = graphene.List(
        graphene.Int, description="The work experience years range of the job position."
    )
    report = graphene.Field(OrganizationJobPositionReportType)
    skills = graphene.List(SkillType)
    fields = graphene.List(FieldType)
    benefits = graphene.List(JobBenefitType)

    @classmethod
    def get_access_object(cls, *args, **kwargs):
        job_position: OrganizationJobPosition = cls.get_obj_from_args(args)
        if not job_position:
            return None

        return job_position.organization

    class Meta:
        model = OrganizationJobPosition
        use_connection = True
        fields = (
            OrganizationJobPosition.id.field.name,
            OrganizationJobPosition.title.field.name,
            OrganizationJobPosition.vaccancy.field.name,
            OrganizationJobPosition.start_at.field.name,
            OrganizationJobPosition.validity_date.field.name,
            OrganizationJobPosition.description.field.name,
            OrganizationJobPosition.degrees.field.name,
            OrganizationJobPosition.languages.field.name,
            OrganizationJobPosition.native_languages.field.name,
            OrganizationJobPosition.required_documents.field.name,
            OrganizationJobPosition.performance_expectation.field.name,
            OrganizationJobPosition.contract_type.field.name,
            OrganizationJobPosition.location_type.field.name,
            OrganizationJobPosition.payment_term.field.name,
            OrganizationJobPosition.working_start_at.field.name,
            OrganizationJobPosition.working_end_at.field.name,
            OrganizationJobPosition.other_benefits.field.name,
            OrganizationJobPosition.days_off.field.name,
            OrganizationJobPosition.job_restrictions.field.name,
            OrganizationJobPosition.employer_questions.field.name,
            OrganizationJobPosition.city.field.name,
            JobPositionAssignment.job_position.field.related_query_name(),
        )
        filter_fields = {
            OrganizationJobPosition.organization.field.name: ["exact"],
            OrganizationJobPosition.title.field.name: ["icontains"],
            OrganizationJobPosition._status.field.name: ["exact"],
            OrganizationJobPosition.start_at.field.name: ["lte", "gte"],
            OrganizationJobPosition.city.field.name: ["exact"],
        }

    def resolve_status(self, info):
        return self.status

    def resolve_age_range(self, info):
        if self.age_range is None:
            return None
        return [self.age_range.lower, self.age_range.upper]

    def resolve_salary_range(self, info):
        if self.salary_range is None:
            return None
        return [self.salary_range.lower, self.salary_range.upper]

    def resolve_work_experience_years_range(self, info):
        if self.work_experience_years_range is None:
            return None
        return [self.work_experience_years_range.lower, self.work_experience_years_range.upper]

    def resolve_report(self, info):
        return self

    def resolve_skills(self, info):
        return self.skills.all()

    def resolve_fields(self, info):
        return self.fields.all()

    def resolve_benefits(self, info):
        return self.benefits.all()

    @classmethod
    def get_queryset(cls, queryset: QuerySet[OrganizationJobPosition], info):
        user = info.context.user
        return queryset.filter(
            **{
                fields_join(
                    OrganizationJobPosition.organization,
                    OrganizationMembership.organization.field.related_query_name(),
                    OrganizationMembership.user,
                ): user
            }
        )


class JobPositionInterviewType(DjangoObjectType):
    class Meta:
        model = JobPositionInterview
        fields = (
            JobPositionInterview.id.field.name,
            JobPositionInterview.interview_date.field.name,
            JobPositionInterview.result_date.field.name,
        )


class JobPositionAssignmentStatusHistoryType(DjangoObjectType):
    class Meta:
        model = JobPositionAssignmentStatusHistory
        fields = (
            JobPositionAssignmentStatusHistory.status.field.name,
            JobPositionAssignmentStatusHistory.created_at.field.name,
        )


class JobPositionAssignmentNode(DjangoObjectType):
    job_seeker = graphene.Field(JobSeekerType)

    class Meta:
        model = JobPositionAssignment
        fields = (
            JobPositionAssignment.id.field.name,
            JobPositionAssignment.status.field.name,
            JobPositionAssignment.created_at.field.name,
            JobPositionInterview.job_position_assignment.field.related_query_name(),
            JobPositionAssignmentStatusHistory.job_position_assignment.field.related_query_name(),
        )

    def resolve_job_seeker(self, info):
        return self.job_seeker
