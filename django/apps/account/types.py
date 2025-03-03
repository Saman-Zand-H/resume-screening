import contextlib
from operator import itemgetter

import graphene
from academy.mixins import CourseUserContextMixin
from academy.types import CourseNode, CourseResultType
from common.decorators import login_required
from common.mixins import ArrayChoiceTypeMixin
from common.models import (
    LanguageProficiencySkill,
    LanguageProficiencyTest,
)
from common.types import (
    BaseFileModelType,
    CityNode,
    DictFieldsObjectType,
    FieldType,
    IndustryNode,
    JobBenefitType,
    LanguageProficiencySkillNode,
    LanguageProficiencyTestNode,
    SkillType,
    UniversityNode,
)
from common.utils import fj
from criteria.mixins import JobAssessmentUserContextMixin
from criteria.models import JobAssessment
from criteria.types import JobAssessmentFilterInput, JobAssessmentType
from cv.types import GeneratedCVContentType, GeneratedCVNode, JobSeekerGeneratedCVType
from graphene_django.converter import (
    convert_choice_field_to_enum,
    convert_choices_to_named_enum_with_descriptions,
)
from graphene_django.filter import DjangoFilterConnectionField
from graphene_django_cud.mutations.create import get_input_fields_for_model
from graphene_django_optimizer import OptimizedDjangoObjectType as DjangoObjectType
from graphql_auth.queries import CountableConnection
from graphql_auth.queries import UserNode as BaseUserNode
from graphql_auth.settings import graphql_auth_settings
from notification.models import InAppNotification

from django.contrib.contenttypes.models import ContentType
from django.db.models import (
    Case,
    Count,
    IntegerField,
    OuterRef,
    Q,
    QuerySet,
    Subquery,
    Value,
    When,
)
from django.db.models.lookups import (
    Exact,
    GreaterThanOrEqual,
    IContains,
    IsNull,
    LessThanOrEqual,
)

from .accesses import JobPositionContainer, OrganizationMembershipContainer
from .filterset import JobPositionAssignmentFilterset, OrganizationEmployeeFilterset
from .mixins import (
    CooperationContextMixin,
    FilterQuerySetByUserMixin,
    ObjectTypeAccessRequiredMixin,
)
from .models import (
    Access,
    CanadaVisa,
    CertificateAndLicense,
    CertificateAndLicenseOfflineVerificationMethod,
    CertificateAndLicenseOnlineVerificationMethod,
    CommunicationMethod,
    Contact,
    DegreeFile,
    Education,
    EducationEvaluationDocumentFile,
    EmployerLetterFile,
    EmployerLetterMethod,
    IEEMethod,
    JobPositionAssignment,
    JobPositionAssignmentStatusHistory,
    JobPositionInterview,
    LanguageCertificate,
    LanguageCertificateValue,
    OfflineMethod,
    OnlineMethod,
    Organization,
    OrganizationEmployee,
    OrganizationEmployeeCooperation,
    OrganizationEmployeePerformanceReport,
    OrganizationEmployeePerformanceReportStatusHistory,
    OrganizationInvitation,
    OrganizationJobPosition,
    OrganizationMembership,
    OrganizationPlatformMessage,
    OrganizationPlatformMessageAttachment,
    PaystubsFile,
    PaystubsMethod,
    PlatformMessageAttachmentCourse,
    PlatformMessageAttachmentCourseResult,
    PlatformMessageAttachmentFile,
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


class InAppNotificationNode(DjangoObjectType):
    class Meta:
        model = InAppNotification
        use_connection = True
        fields = (
            InAppNotification.id.field.name,
            InAppNotification.title.field.name,
            InAppNotification.body.field.name,
            InAppNotification.read_at.field.name,
            InAppNotification.created.field.name,
            InAppNotification.modified.field.name,
        )
        filter_fields = {
            InAppNotification.read_at.field.name: ["isnull"],
        }


class ContactType(DjangoObjectType):
    class Meta:
        model = Contact
        fields = (
            Contact.id.field.name,
            Contact.type.field.name,
            Contact.value.field.name,
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


class IEEMethodType(DjangoObjectType):
    class Meta:
        model = IEEMethod
        fields = (
            IEEMethod.id.field.name,
            IEEMethod.education_evaluation_document.field.name,
        )


class JobSeekerEducationType(DjangoObjectType):
    communicationmethod = graphene.Field(CommunicationMethodType)
    ieemethod = graphene.Field(IEEMethodType)

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

    def resolve_communicationmethod(self, info):
        return CommunicationMethod.objects.filter(**{fj(CommunicationMethod.education): self}).first()

    def resolve_ieemethod(self, info):
        return IEEMethod.objects.filter(**{fj(IEEMethod.education): self}).first()


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
            *(m.get_related_name() for m in WorkExperience.get_method_models()),
        )


class JobSeekerLanguageCertificateType(DjangoObjectType):
    test = graphene.Field(LanguageProficiencyTestNode)

    class Meta:
        model = LanguageCertificate
        fields = (
            LanguageCertificate.id.field.name,
            LanguageCertificate.language.field.name,
            LanguageCertificate.issued_at.field.name,
            LanguageCertificate.expired_at.field.name,
            LanguageCertificate.status.field.name,
            *(m.get_related_name() for m in LanguageCertificate.get_method_models()),
        )

    def resolve_test(self, info):
        return self.test


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
            *(m.get_related_name() for m in CertificateAndLicense.get_method_models()),
        )


class JobSeekerProfilePrimitiveType(DjangoObjectType):
    class Meta:
        model = Profile
        fields = (
            Profile.avatar.field.name,
            Profile.score.field.name,
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
            Profile.city.field.name,
            Profile.birth_date.field.name,
            Profile.gender.field.name,
        )

    def resolve_contacts(self, info):
        return self.contactable.contacts.all()


class JobSeekerPrimitiveType(DjangoObjectType):
    profile = graphene.Field(JobSeekerProfilePrimitiveType)
    workexperiences = graphene.List(JobSeekerWorkExperienceType)

    class Meta:
        model = User
        fields = (
            User.first_name.field.name,
            User.last_name.field.name,
        )

    def resolve_profile(self, info):
        return self.profile

    def resolve_workexperiences(self, info):
        return self.workexperiences.all().order_by("-id")


class JobSeekerType(DjangoObjectType):
    profile = graphene.Field(JobSeekerProfileType)
    educations = graphene.List(JobSeekerEducationType)
    workexperiences = graphene.List(JobSeekerWorkExperienceType)
    languagecertificates = graphene.List(JobSeekerLanguageCertificateType)
    certificateandlicenses = graphene.List(JobSeekerCertificateAndLicenseType)
    cv = graphene.Field(JobSeekerGeneratedCVType)
    cv_content = graphene.Field(GeneratedCVContentType)

    class Meta:
        model = User
        fields = (
            User.first_name.field.name,
            User.last_name.field.name,
            User.email.field.name,
            Resume.user.field.related_query_name(),
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

    def resolve_cv(self, info):
        return self.cv if hasattr(self, "cv") else None

    def resolve_cv_contents(self, info):
        return self.cv_contents.latest("id")


class JobSeekerUnionType(graphene.Union):
    class Meta:
        types = (JobSeekerType, JobSeekerPrimitiveType)

    def resolve_type(self, info):
        # TODO: Check if user has paid for the service, return JobSeekerType,
        # Otherwise return JobSeekerPrimitiveType
        status = getattr(info.context, "assignment_status", None)
        if status in JobPositionAssignment.get_job_seeker_specific_statuses():
            return JobSeekerPrimitiveType
        return JobSeekerType


class EmployeeType(DjangoObjectType):
    profile = graphene.Field(JobSeekerProfileType)
    educations = graphene.List(JobSeekerEducationType)
    workexperiences = graphene.List(JobSeekerWorkExperienceType)
    languagecertificates = graphene.List(JobSeekerLanguageCertificateType)
    certificateandlicenses = graphene.List(JobSeekerCertificateAndLicenseType)
    cv = graphene.Field(JobSeekerGeneratedCVType)
    cv_content = graphene.Field(GeneratedCVContentType)
    job_assessments = graphene.List(
        JobAssessmentType, filters=graphene.Argument(JobAssessmentFilterInput, required=False)
    )
    courses = DjangoFilterConnectionField(CourseNode)

    class Meta:
        model = User
        fields = (
            User.first_name.field.name,
            User.last_name.field.name,
            User.email.field.name,
            Resume.user.field.related_query_name(),
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

    def resolve_cv(self, info):
        return self.cv if hasattr(self, "cv") else None

    def resolve_cv_contents(self, info):
        return self.cv_contents.latest("id")

    def resolve_job_assessments(self, info, filters=None):
        qs = JobAssessment.objects.related_to_user(self)
        JobAssessmentUserContextMixin.set_obj_context(info.context, self)
        if filters:
            if filters.required is not None:
                qs = qs.filter_by_required(filters.required, self.profile.interested_jobs.all())
        return qs.order_by("-id")

    def resolve_courses(self, info, **kwargs):
        CourseUserContextMixin.set_obj_context(info.context, self)
        return CourseNode._meta.model.objects


class ProfileType(ArrayChoiceTypeMixin, DjangoObjectType):
    completion_percentage = graphene.Float(source=Profile.completion_percentage.fget.__name__)
    contacts = graphene.List(ContactType)
    job_type = graphene.List(
        convert_choice_field_to_enum(Profile.job_type_exclude.field.base_field),
        source=Profile.job_type.fget.__name__,
    )
    job_location_type = graphene.List(
        convert_choice_field_to_enum(Profile.job_location_type_exclude.field.base_field),
        source=Profile.job_location_type.fget.__name__,
    )

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


class EducationMethodFieldTypes(graphene.ObjectType):
    method = graphene.String()
    field = graphene.String()


class EducationNode(FilterQuerySetByUserMixin, DjangoObjectType):
    communicationmethod = graphene.Field(CommunicationMethodType)
    ieemethod = graphene.Field(IEEMethodType)

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
        )

    def resolve_communicationmethod(self, info):
        return CommunicationMethod.objects.filter(**{fj(CommunicationMethod.education): self}).first()

    def resolve_ieemethod(self, info):
        return IEEMethod.objects.filter(**{fj(IEEMethod.education): self}).first()


class EducationAIType(DictFieldsObjectType):
    dict_fields = get_input_fields_for_model(
        Education,
        fields=(
            fields := (
                Education.degree.field.name,
                Education.start.field.name,
                Education.end.field.name,
            )
        ),
        optional_fields=fields,
        exclude=tuple(),
    )

    field = graphene.Field(FieldType)
    university = graphene.Field(UniversityNode)
    city = graphene.Field(CityNode)


class IEEMethodAIType(DictFieldsObjectType):
    dict_fields = get_input_fields_for_model(
        IEEMethod,
        fields=(fields := (IEEMethod.evaluator.field.name,)),
        optional_fields=fields,
        exclude=tuple(),
    )


class CommunicationMethodAIType(DictFieldsObjectType):
    dict_fields = get_input_fields_for_model(
        CommunicationMethod,
        fields=(
            fields := (
                CommunicationMethod.website.field.name,
                CommunicationMethod.email.field.name,
                CommunicationMethod.department.field.name,
                CommunicationMethod.person.field.name,
            )
        ),
        optional_fields=fields,
        exclude=tuple(),
    )


class EducationVerificationMethodType(graphene.Union):
    class Meta:
        types = (IEEMethodAIType, CommunicationMethodAIType)

    def resolve_type(self, info):
        model = getattr(info.context, "model", None)
        if model == EducationEvaluationDocumentFile:
            return IEEMethodAIType
        elif model == DegreeFile:
            return CommunicationMethodAIType
        return None


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


class WorkExperienceAIType(DictFieldsObjectType):
    dict_fields = get_input_fields_for_model(
        WorkExperience,
        fields=(
            fields := (
                WorkExperience.job_title.field.name,
                WorkExperience.grade.field.name,
                WorkExperience.start.field.name,
                WorkExperience.end.field.name,
                WorkExperience.organization.field.name,
                WorkExperience.skills.field.name,
            )
        ),
        optional_fields=fields,
        exclude=tuple(),
    )

    city = graphene.Field(CityNode)
    industry = graphene.Field(IndustryNode)


class ReferenceCheckEmployerAIType(DictFieldsObjectType):
    dict_fields = get_input_fields_for_model(
        ReferenceCheckEmployer,
        fields=(
            fields := (
                ReferenceCheckEmployer.name.field.name,
                ReferenceCheckEmployer.email.field.name,
                ReferenceCheckEmployer.phone_number.field.name,
                ReferenceCheckEmployer.position.field.name,
            )
        ),
        optional_fields=fields,
        exclude=tuple(),
    )


class PaystubsMethodType(DjangoObjectType):
    class Meta:
        model = PaystubsMethod
        fields = (
            PaystubsMethod.id.field.name,
            PaystubsMethod.paystubs.field.name,
        )


class PaystubsMethodAIType(graphene.ObjectType):
    id = graphene.ID()


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


class EmployerLetterMethodType(DjangoObjectType):
    employers = graphene.List(ReferenceCheckEmployerType)

    class Meta:
        model = EmployerLetterMethod
        fields = (
            EmployerLetterMethod.id.field.name,
            EmployerLetterMethod.employer_letter.field.name,
            ReferenceCheckEmployer.work_experience_verification.field.related_query_name(),
        )

    def resolve_employers(self, info):
        return ReferenceCheckEmployer.objects.filter(**{fj(ReferenceCheckEmployer.work_experience_verification): self})


class WorkExperienceVerificationMethodType(graphene.Union):
    class Meta:
        types = (ReferenceCheckEmployerAIType, PaystubsMethodAIType)

    def resolve_type(self, info):
        model = getattr(info.context, "model", None)
        if model == PaystubsFile:
            return PaystubsMethodAIType
        elif model == EmployerLetterFile:
            return ReferenceCheckEmployerAIType
        return None


class LanguageCertificateValueNode(DjangoObjectType):
    skill = graphene.Field(LanguageProficiencySkillNode)

    class Meta:
        model = LanguageCertificateValue
        fields = (
            LanguageCertificateValue.id.field.name,
            LanguageCertificateValue.value.field.name,
        )

    def resolve_skill(self, info):
        return self.skill


class LanguageCertificateNode(FilterQuerySetByUserMixin, DjangoObjectType):
    test = graphene.Field(LanguageProficiencyTestNode)
    values = graphene.List(LanguageCertificateValueNode)

    class Meta:
        model = LanguageCertificate
        use_connection = True
        fields = (
            LanguageCertificate.id.field.name,
            LanguageCertificate.language.field.name,
            LanguageCertificate.status.field.name,
            LanguageCertificate.issued_at.field.name,
            LanguageCertificate.expired_at.field.name,
            LanguageCertificate.allow_self_verification.field.name,
            LanguageCertificate.status.field.name,
            *(m.get_related_name() for m in LanguageCertificate.get_method_models()),
        )

    def resolve_test(self, info):
        return self.test

    def resolve_values(self, info):
        return LanguageCertificateValue.objects.filter(**{fj(LanguageCertificateValue.language_certificate): self})


class LanguageCertificateValueSkillAIType(DictFieldsObjectType):
    dict_fields = get_input_fields_for_model(
        LanguageProficiencySkill,
        fields=(
            fields := (
                LanguageProficiencySkill.id.field.name,
                LanguageProficiencySkill.slug.field.name,
                LanguageProficiencySkill.skill_name.field.name,
            )
        ),
        optional_fields=fields,
        exclude=tuple(),
        ignore_primary_key=False,
    )


class LanguageCertificateTestAIType(DictFieldsObjectType):
    dict_fields = get_input_fields_for_model(
        LanguageProficiencyTest,
        fields=(
            fields := (
                LanguageProficiencyTest.id.field.name,
                LanguageProficiencyTest.title.field.name,
            )
        ),
        optional_fields=fields,
        exclude=tuple(),
        ignore_primary_key=False,
    )


class LanguageCertificateValueAIType(DictFieldsObjectType):
    dict_fields = get_input_fields_for_model(
        LanguageCertificateValue,
        fields=(fields := (LanguageCertificateValue.value.field.name,)),
        optional_fields=fields,
        exclude=tuple(),
    )

    skill = graphene.Field(LanguageCertificateValueSkillAIType)


class LanguageCertificateAIType(DictFieldsObjectType):
    dict_fields = get_input_fields_for_model(
        LanguageCertificate,
        fields=(
            fields := (
                LanguageCertificate.language.field.name,
                LanguageCertificate.issued_at.field.name,
                LanguageCertificate.expired_at.field.name,
            )
        ),
        optional_fields=fields,
        exclude=tuple(),
    )

    test = graphene.Field(LanguageCertificateTestAIType)
    values = graphene.List(LanguageCertificateValueAIType)


class LanguageCertificateOfflineVerificationMethodType(DjangoObjectType):
    class Meta:
        model = OfflineMethod
        fields = (OfflineMethod.id.field.name, OfflineMethod.certificate_file.field.name)


class LanguageCertificateOnlineVerificationMethodType(DjangoObjectType):
    class Meta:
        model = OnlineMethod
        fields = (OnlineMethod.id.field.name, OnlineMethod.certificate_link.field.name)


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
            *(m.get_related_name() for m in CertificateAndLicense.get_method_models()),
        )


class CertificateAndLicenseAIType(DictFieldsObjectType):
    dict_fields = get_input_fields_for_model(
        CertificateAndLicense,
        fields=(
            fields := (
                CertificateAndLicense.title.field.name,
                CertificateAndLicense.certifier.field.name,
                CertificateAndLicense.issued_at.field.name,
                CertificateAndLicense.expired_at.field.name,
            )
        ),
        optional_fields=fields,
        exclude=tuple(),
    )


class CertificateAndLicenseOfflineVerificationMethodType(DjangoObjectType):
    class Meta:
        model = CertificateAndLicenseOfflineVerificationMethod
        fields = (
            CertificateAndLicenseOfflineVerificationMethod.id.field.name,
            CertificateAndLicenseOfflineVerificationMethod.certificate_file.field.name,
        )


class CertificateAndLicenseOnlineVerificationMethodType(DjangoObjectType):
    class Meta:
        model = CertificateAndLicenseOnlineVerificationMethod
        fields = (
            CertificateAndLicenseOnlineVerificationMethod.id.field.name,
            CertificateAndLicenseOnlineVerificationMethod.certificate_link.field.name,
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


class UserTaskType(DjangoObjectType):
    @classmethod
    @login_required
    def get_queryset(cls, queryset: QuerySet[UserTask], info):
        return (
            queryset.filter(**{fj(UserTask.user): info.context.user})
            .order_by(fj(UserTask.task_name), f"-{fj(UserTask.created)}")
            .distinct(fj(UserTask.task_name))
        )

    class Meta:
        model = UserTask
        fields = (
            UserTask.task_name.field.name,
            UserTask.status.field.name,
        )


class OrganizationType(DjangoObjectType):
    email = graphene.String()
    contacts = graphene.List(ContactType)
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
            Organization.city.field.name,
            Organization.about.field.name,
            Organization.status.field.name,
            OrganizationInvitation.organization.field.related_query_name(),
            OrganizationMembership.organization.field.related_query_name(),
        )

    def resolve_email(self, info):
        return self.user.email

    def resolve_contacts(self, info):
        return self.contactable.contacts.all()

    def resolve_has_financial_data(self, info):
        return True


class JobSeekerOrganizationType(DjangoObjectType):
    contacts = graphene.List(ContactType)

    class Meta:
        model = Organization
        fields = (
            Organization.id.field.name,
            Organization.name.field.name,
            Organization.logo.field.name,
            Organization.short_name.field.name,
            Organization.established_at.field.name,
            Organization.size.field.name,
            Organization.city.field.name,
        )

    def resolve_contacts(self, info):
        return self.contactable.contacts.all()


class OrganizationMembershipType(ObjectTypeAccessRequiredMixin, DjangoObjectType):
    fields_access = {
        "__all__": OrganizationMembershipContainer.get_accesses(),
    }

    user = graphene.Field(OrganizationMembershipUserType, source=OrganizationMembership.user.field.name)
    accessed_roles = graphene.List(RoleType)

    def resolve_accessed_roles(self, info):
        return Role.objects.filter(
            (
                Q(**{fj(Role.managed_by_id): self.organization_id})
                & Q(**{fj(Role.managed_by_model): ContentType.objects.get_for_model(Organization)})
            )
            | (
                Q(**{fj(Role.managed_by_id, IsNull.lookup_name): True}) & Q(**{fj(Role.managed_by_model, IsNull): True})
            ),
        ).distinct()

    @classmethod
    def get_access_object(cls, *args, **kwargs):
        membership: OrganizationMembership = cls.get_obj_from_args(args)
        if not membership:
            return None

        return membership.organization

    organization = graphene.Field(OrganizationType)

    class Meta:
        model = OrganizationMembership
        fields = (OrganizationMembership.role.field.name,)

    def resolve_organization(self, info):
        return self.organization


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

    organization = graphene.Field(OrganizationType)

    class Meta:
        model = OrganizationInvitation
        fields = (
            OrganizationInvitation.id.field.name,
            OrganizationInvitation.email.field.name,
            OrganizationInvitation.role.field.name,
            OrganizationInvitation.created_at.field.name,
            OrganizationInvitation.created_by.field.name,
        )

    def resolve_organization(self, info):
        return self.organization

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
            JobPositionAssignment.objects.filter(**{fj(JobPositionAssignment.job_position): self})
            .values(
                JobPositionAssignment.status.field.name,
            )
            .annotate(count=Count(JobPositionAssignment.status.field.name))
        )

        return [
            JobPositionAssignmentStatusCountType(status=item["status"].upper(), count=item["count"])
            for item in status_counts
        ]


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
            JobPositionInterview.assignment_status_history.field.related_query_name(),
        )


class JobPositionAssignmentNode(ObjectTypeAccessRequiredMixin, ArrayChoiceTypeMixin, DjangoObjectType):
    fields_access = {
        "__all__": JobPositionContainer.get_accesses(),
    }

    job_seeker = graphene.Field(JobSeekerUnionType)

    @classmethod
    def get_access_object(cls, *args, **kwargs):
        assignment: JobPositionAssignment = cls.get_obj_from_args(args)
        if not assignment:
            return None

        return assignment.job_position.organization

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
        info.context.assignment_status = self.status
        return self.job_seeker


class OrganizationJobPositionNode(ObjectTypeAccessRequiredMixin, ArrayChoiceTypeMixin, DjangoObjectType):
    fields_access = {
        "__all__": JobPositionContainer.get_accesses(),
    }
    age_range = graphene.List(graphene.Int)
    salary_range = graphene.List(graphene.Int)
    work_experience_years_range = graphene.List(graphene.Int)
    report = graphene.Field(OrganizationJobPositionReportType)
    skills = graphene.List(SkillType)
    fields = graphene.List(FieldType)
    benefits = graphene.List(JobBenefitType)
    is_editable = graphene.Boolean()

    assignments = graphene.List(JobPositionAssignmentNode)

    @classmethod
    def get_access_object(cls, *args, **kwargs):
        job_position: OrganizationJobPosition = cls.get_obj_from_args(args)
        if not job_position:
            return None

        return job_position.organization

    class Meta:
        model = OrganizationJobPosition
        use_connection = True
        connection_class = CountableConnection
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
            OrganizationJobPosition.status.field.name,
            OrganizationJobPosition.working_start_at.field.name,
            OrganizationJobPosition.working_end_at.field.name,
            OrganizationJobPosition.other_benefits.field.name,
            OrganizationJobPosition.days_off.field.name,
            OrganizationJobPosition.job_restrictions.field.name,
            OrganizationJobPosition.employer_questions.field.name,
            OrganizationJobPosition.city.field.name,
        )
        filter_fields = {
            OrganizationJobPosition.organization.field.name: [Exact.lookup_name],
            OrganizationJobPosition.title.field.name: [IContains.lookup_name],
            OrganizationJobPosition.status.field.name: [Exact.lookup_name],
            OrganizationJobPosition.start_at.field.name: [LessThanOrEqual.lookup_name, GreaterThanOrEqual.lookup_name],
            OrganizationJobPosition.city.field.name: [Exact.lookup_name],
            fj(
                JobPositionAssignment.job_position.field.related_query_name(),
                JobPositionAssignment.status.field.name,
            ): [Exact.lookup_name],
        }

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

    def resolve_is_editable(self, info):
        return self.is_editable

    def resolve_assignments(self, info):
        return self.assignments.all()

    @classmethod
    def get_queryset(cls, queryset: QuerySet[OrganizationJobPosition], info):
        user = info.context.user
        return queryset.filter(
            **{
                fj(
                    OrganizationJobPosition.organization,
                    OrganizationMembership.organization.field.related_query_name(),
                    OrganizationMembership.user,
                ): user
            }
        ).order_by("-id")


class JobSeekerJobPositionType(DjangoObjectType):
    age_range = graphene.List(graphene.Int)
    salary_range = graphene.List(graphene.Int)
    work_experience_years_range = graphene.List(graphene.Int)
    report = graphene.Field(OrganizationJobPositionReportType)
    skills = graphene.List(SkillType)
    fields = graphene.List(FieldType)
    benefits = graphene.List(JobBenefitType)
    organization = graphene.Field(JobSeekerOrganizationType)

    class Meta:
        model = OrganizationJobPosition
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
            OrganizationJobPosition.status.field.name,
        )

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

    def resolve_organization(self, info):
        return self.organization


class JobSeekerJobPositionAssignmentNode(ArrayChoiceTypeMixin, DjangoObjectType):
    job_position = graphene.Field(JobSeekerJobPositionType)

    class Meta:
        model = JobPositionAssignment
        use_connection = True
        fields = (
            JobPositionAssignment.id.field.name,
            JobPositionAssignment.status.field.name,
            JobPositionAssignment.created_at.field.name,
            JobPositionInterview.job_position_assignment.field.related_query_name(),
            JobPositionAssignmentStatusHistory.job_position_assignment.field.related_query_name(),
        )

        filterset_class = JobPositionAssignmentFilterset

    def resolve_job_position(self, info):
        return self.job_position


class OrganizationEmployeePerformanceReportStatusHistoryType(DjangoObjectType):
    class Meta:
        model = OrganizationEmployeePerformanceReportStatusHistory
        fields = (
            OrganizationEmployeePerformanceReportStatusHistory.status.field.name,
            OrganizationEmployeePerformanceReportStatusHistory.created_at.field.name,
        )


class OrganizationEmployeePerformanceReportNode(CooperationContextMixin, ArrayChoiceTypeMixin, DjangoObjectType):
    class Meta:
        model = OrganizationEmployeePerformanceReport
        use_connection = True
        connection_class = CountableConnection
        fields = (
            OrganizationEmployeePerformanceReport.id.field.name,
            OrganizationEmployeePerformanceReport.status.field.name,
            OrganizationEmployeePerformanceReport.title.field.name,
            OrganizationEmployeePerformanceReport.report_summary.field.name,
            OrganizationEmployeePerformanceReport.report_text.field.name,
            OrganizationEmployeePerformanceReport.date.field.name,
            OrganizationEmployeePerformanceReportStatusHistory.organization_employee_performance_report.field.related_query_name(),
        )

        filter_fields = {
            OrganizationEmployeePerformanceReport.date.field.name: [
                LessThanOrEqual.lookup_name,
                GreaterThanOrEqual.lookup_name,
            ]
        }

    @classmethod
    def get_queryset(cls, queryset, info):
        return queryset.filter(
            **{
                fj(
                    OrganizationEmployeePerformanceReport.organization_employee_cooperation,
                ): cls.get_obj_context(info.context)
            }
        )


class OrganizationPlatformMessageNode(CooperationContextMixin, ArrayChoiceTypeMixin, DjangoObjectType):
    class Meta:
        model = OrganizationPlatformMessage
        use_connection = True
        fields = (
            OrganizationPlatformMessage.id.field.name,
            OrganizationPlatformMessage.source.field.name,
            OrganizationPlatformMessage.title.field.name,
            OrganizationPlatformMessage.text.field.name,
            OrganizationPlatformMessage.read_at.field.name,
            OrganizationPlatformMessage.created.field.name,
            OrganizationPlatformMessageAttachment.organization_platform_message.field.related_query_name(),
        )

        filter_fields = {}

    @classmethod
    def get_queryset(cls, queryset, info):
        return queryset.filter(
            **{
                fj(
                    OrganizationPlatformMessage.organization_employee_cooperation,
                ): cls.get_obj_context(info.context),
                OrganizationPlatformMessage.assignee_type.field.name: info.context.user.registration_type,
            }
        )


AttachmentType = convert_choices_to_named_enum_with_descriptions(
    "AttachmentType",
    sorted(
        (
            (model.SLUG, model._meta.verbose_name)
            for model in OrganizationPlatformMessageAttachment.get_attachment_models()
        ),
        key=itemgetter(0),
    ),
)


class OrganizationPlatformMessageAttachmentType(DjangoObjectType):
    attachment_type = AttachmentType()
    file = graphene.Field(BaseFileModelType)
    course = graphene.Field(CourseNode)
    course_result = graphene.Field(CourseResultType)

    class Meta:
        model = OrganizationPlatformMessageAttachment
        fields = (
            OrganizationPlatformMessageAttachment.id.field.name,
            OrganizationPlatformMessageAttachment.text.field.name,
        )

    def resolve_attachment_type(self, info):
        if self.attachment_type:
            return AttachmentType[self.attachment_type]

    def resolve_file(self, info):
        return getattr(
            PlatformMessageAttachmentFile.objects.filter(pk=self.pk).first(),
            fj(PlatformMessageAttachmentFile.file),
            None,
        )

    def resolve_course(self, info):
        return getattr(
            PlatformMessageAttachmentCourse.objects.filter(pk=self.pk).first(),
            fj(PlatformMessageAttachmentCourse.course),
            None,
        )

    def resolve_course_result(self, info):
        return getattr(
            PlatformMessageAttachmentCourseResult.objects.filter(pk=self.pk).first(),
            fj(PlatformMessageAttachmentCourseResult.course_result),
            None,
        )


class OrganizationEmployeeCooperationType(ArrayChoiceTypeMixin, DjangoObjectType):
    job_position = graphene.Field(OrganizationJobPositionNode)
    platform_messages = DjangoFilterConnectionField(OrganizationPlatformMessageNode)
    performance_report = DjangoFilterConnectionField(OrganizationEmployeePerformanceReportNode)
    employer_satisfaction_rate = graphene.Float()

    class Meta:
        model = OrganizationEmployeeCooperation
        fields = (
            OrganizationEmployeeCooperation.id.field.name,
            OrganizationEmployeeCooperation.status.field.name,
            OrganizationEmployeeCooperation.start_at.field.name,
            OrganizationEmployeeCooperation.end_at.field.name,
            OrganizationEmployeeCooperation.created_at.field.name,
        )

    def resolve_job_position(self, info):
        return self.job_position_assignment.job_position

    def resolve_platform_messages(self, info, **kwargs):
        CooperationContextMixin.set_obj_context(info.context, self)
        return OrganizationPlatformMessage.objects.filter(
            **{fj(OrganizationPlatformMessage.organization_employee_cooperation): self}
        )

    def resolve_performance_report(self, info, **kwargs):
        CooperationContextMixin.set_obj_context(info.context, self)
        return OrganizationEmployeePerformanceReport.objects.filter(
            **{fj(OrganizationEmployeePerformanceReport.organization_employee_cooperation): self}
        )

    def resolve_employer_satisfaction_rate(self, info):
        return self.employer_satisfaction_rate


class JobSeekerCooperationType(DjangoObjectType):
    job_position = graphene.Field(JobSeekerJobPositionType)
    platform_messages = DjangoFilterConnectionField(OrganizationPlatformMessageNode)
    performance_report = DjangoFilterConnectionField(OrganizationEmployeePerformanceReportNode)
    employer_satisfaction_rate = graphene.Float()

    class Meta:
        model = OrganizationEmployeeCooperation
        fields = (
            OrganizationEmployeeCooperation.id.field.name,
            OrganizationEmployeeCooperation.status.field.name,
            OrganizationEmployeeCooperation.start_at.field.name,
            OrganizationEmployeeCooperation.end_at.field.name,
            OrganizationEmployeeCooperation.created_at.field.name,
        )

    def resolve_job_position(self, info):
        return self.job_position_assignment.job_position

    def resolve_platform_messages(self, info, **kwargs):
        CooperationContextMixin.set_obj_context(info.context, self)
        return OrganizationPlatformMessage.objects.filter(
            **{fj(OrganizationPlatformMessage.organization_employee_cooperation): self}
        )

    def resolve_performance_report(self, info, **kwargs):
        CooperationContextMixin.set_obj_context(info.context, self)
        return OrganizationEmployeePerformanceReport.objects.filter(
            **{fj(OrganizationEmployeePerformanceReport.organization_employee_cooperation): self}
        )

    def resolve_employer_satisfaction_rate(self, info):
        return self.employer_satisfaction_rate


class OrganizationEmployeeNode(ArrayChoiceTypeMixin, DjangoObjectType):
    employee = graphene.Field(EmployeeType)
    cooperations = graphene.List(OrganizationEmployeeCooperationType)

    class Meta:
        model = OrganizationEmployee
        use_connection = True
        fields = (OrganizationEmployee.id.field.name,)
        filterset_class = OrganizationEmployeeFilterset

    def resolve_employee(self, info):
        return self.user

    def resolve_cooperations(self, info):
        return self.cooperations.all()

    @classmethod
    def get_queryset(cls, queryset: QuerySet[OrganizationEmployee], info):
        user = info.context.user
        return (
            queryset.filter(
                **{
                    fj(
                        OrganizationEmployee.organization,
                        OrganizationMembership.organization.field.related_query_name(),
                        OrganizationMembership.user,
                    ): user
                }
            )
            .annotate(
                last_cooperation_status=Subquery(
                    (
                        OrganizationEmployeeCooperation.objects.filter(
                            **{
                                fj(OrganizationEmployeeCooperation.employee): OuterRef(
                                    OrganizationEmployeeCooperation._meta.pk.attname
                                )
                            }
                        )
                        .order_by(f"-{OrganizationEmployeeCooperation._meta.pk.attname}")
                        .values(fj(OrganizationEmployeeCooperation.status))[:1]
                    )
                ),
                status_order=Case(
                    *[
                        When(last_cooperation_status=status, then=Value(order))
                        for order, status in enumerate(OrganizationEmployeeCooperation.get_status_order())
                    ],
                    output_field=IntegerField(),
                ),
            )
            .distinct()
            .order_by("status_order", "-created")
        )


class JobSeekerEmployeeType(DjangoObjectType):
    organization = graphene.Field(JobSeekerOrganizationType)
    cooperations = graphene.Field(JobSeekerCooperationType)

    class Meta:
        model = OrganizationEmployee
        fields = (OrganizationEmployee.id.field.name,)

    def resolve_organization(self, info):
        return self.organization

    def resolve_cooperations(self, info):
        return self.cooperations.filter(end_at__isnull=True).latest("created_at")


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
    cv = graphene.Field(GeneratedCVNode)
    notifications = graphene.List(InAppNotificationNode)
    job_position_assignments = DjangoFilterConnectionField(JobSeekerJobPositionAssignmentNode)
    current_employement = graphene.Field(JobSeekerEmployeeType)
    support_tickets = graphene.List(SupportTicketType)

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
            UserTask.user.field.related_query_name(),
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

    def resolve_cv(self, info):
        return self.cv if hasattr(self, "cv") else None

    def resolve_notifications(self, info):
        return InAppNotification.objects.filter(**{fj(InAppNotification.user): self}).order_by(
            f"-{fj(InAppNotification.created)}"
        )

    def resolve_job_position_assignments(self, info, **kwargs):
        return JobPositionAssignment.objects.filter(**{fj(JobPositionAssignment.job_seeker): self}).order_by(
            f"-{fj(JobPositionAssignment.created_at)}"
        )

    def resolve_current_employement(self, info):
        return self.organization_employees.filter(cooperations__end_at__isnull=True).latest("cooperations__created_at")

    def resolve_support_tickets(self, info, **kwargs):
        return SupportTicket.objects.filter(**{fj(SupportTicket.user): self}).order_by(f"-{fj(SupportTicket.created)}")
