from academy.models import Course, CourseResult
from cities_light.models import City
from common.models import Field
from common.utils import fj
from graphql_auth.models import UserStatus
from import_export.admin import ExportMixin

from django.contrib import admin, messages
from django.contrib.admin import register
from django.contrib.auth.admin import UserAdmin as UserAdminBase
from django.contrib.contenttypes.admin import GenericStackedInline
from django.db.models import QuerySet
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from ..forms import OrganizationUserCreationForm, UserChangeForm
from ..models import (
    Access,
    CanadaVisa,
    CertificateAndLicense,
    CertificateAndLicenseOfflineVerificationMethod,
    CertificateAndLicenseOnlineVerificationMethod,
    CommunicateOrganizationMethod,
    CommunicationMethod,
    Contact,
    Contactable,
    DNSTXTRecordMethod,
    Education,
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
    OrganizationEmployeeCooperationStatusHistory,
    OrganizationEmployeePerformanceReport,
    OrganizationEmployeePerformanceReportStatusHistory,
    OrganizationInvitation,
    OrganizationJobPosition,
    OrganizationJobPositionStatusHistory,
    OrganizationMembership,
    OrganizationPlatformMessage,
    OrganizationPlatformMessageAttachment,
    PaystubsMethod,
    PerformanceReportAnswer,
    PerformanceReportQuestion,
    PlatformMessageAttachmentCourse,
    PlatformMessageAttachmentCourseResult,
    PlatformMessageAttachmentFile,
    Profile,
    ReferenceCheckEmployer,
    Referral,
    ReferralUser,
    Resume,
    Role,
    RoleAccess,
    SupportTicket,
    SupportTicketCategory,
    UploadCompanyCertificateMethod,
    UploadFileToWebsiteMethod,
    User,
    UserDevice,
    UserTask,
    WorkExperience,
)
from ..scores import UserScorePack
from ..tasks import get_certificate_text, set_user_resume_json, user_task_runner
from .resources import (
    CertificateAndLicenseResource,
    EducationResource,
    LanguageCertificateResource,
    ProfileResource,
    WorkExperienceResource,
)


class AccessInline(admin.StackedInline):
    model = Access
    extra = 1
    fields = (Access.slug.field.name, Access.title.field.name)


@register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = (Role.slug.field.name, Role.title.field.name, Role.managed_by.name)
    search_fields = (Role.slug.field.name, Role.title.field.name)


@register(Access)
class AccessAdmin(admin.ModelAdmin):
    list_display = (Access.slug.field.name, Access.title.field.name)
    search_fields = (Access.slug.field.name, Access.title.field.name)


@register(RoleAccess)
class RoleAccessAdmin(admin.ModelAdmin):
    list_display = (
        RoleAccess.role.field.name,
        RoleAccess.access.field.name,
    )
    autocomplete_fields = (RoleAccess.role.field.name, RoleAccess.access.field.name)


@register(User)
class UserAdmin(UserAdminBase):
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (User.USERNAME_FIELD, "usable_password", "password1", "password2"),
            },
        ),
    )
    form = UserChangeForm
    list_display = (
        User.USERNAME_FIELD,
        User.first_name.field.name,
        User.last_name.field.name,
        User.is_staff.field.name,
        User.registration_type.field.name,
    )
    search_fields = (User.EMAIL_FIELD, User.first_name.field.name, User.last_name.field.name)

    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)
        fieldsets = list(self.fieldsets)
        fieldsets[0] = (
            None,
            {"fields": (User.USERNAME_FIELD, User.password.field.name)},
        )
        fieldsets[1] = (
            _("Personal info"),
            {
                "fields": (
                    User.first_name.field.name,
                    User.last_name.field.name,
                    User.username.field.name,
                    User.registration_type.field.name,
                )
            },
        )
        self.fieldsets = tuple(fieldsets)


@register(UserDevice)
class UserDeviceIDAdmin(admin.ModelAdmin):
    list_display = (
        UserDevice.device_id.field.name,
        UserDevice.created.field.name,
        UserDevice.user.fget.__name__,
    )
    readonly_fields = (UserDevice.user.fget.__name__,)
    search_fields = (UserDevice.device_id.field.name,)
    autocomplete_fields = (UserDevice.refresh_token.field.name,)


@register(UserStatus)
class UserStatusAdmin(admin.ModelAdmin):
    list_display = (
        UserStatus.user.field.name,
        UserStatus.verified.field.name,
        UserStatus.archived.field.name,
        UserStatus.secondary_email.field.name,
    )
    search_fields = (fj(UserStatus.user, User.email),)
    list_filter = (
        UserStatus.verified.field.name,
        UserStatus.archived.field.name,
    )
    autocomplete_fields = (UserStatus.user.field.name,)


class ProfileInterestedJobsInline(admin.TabularInline):
    model = Profile.interested_jobs.through
    extra = 1
    raw_id_fields = (Profile.interested_jobs.through.job.field.name,)
    verbose_name = _("Interested Job")
    verbose_name_plural = _("Interested Jobs")


@register(Profile)
class ProfileAdmin(ExportMixin, admin.ModelAdmin):
    resource_classes = [ProfileResource]
    list_display = (
        Profile.user.field.name,
        Profile.height.field.name,
        Profile.weight.field.name,
        Profile.skin_color.field.name,
        Profile.hair_color.field.name,
        Profile.eye_color.field.name,
    )
    search_fields = (fj(Profile.user, User.email),)
    list_filter = (
        Profile.height.field.name,
        Profile.weight.field.name,
        Profile.skin_color.field.name,
        Profile.hair_color.field.name,
    )
    autocomplete_fields = (
        Profile.user.field.name,
        Profile.skills.field.name,
        Profile.city.field.name,
        Profile.job_cities.field.name,
        Profile.contactable.field.name,
    )
    raw_id_fields = (
        Profile.avatar.field.name,
        Profile.full_body_image.field.name,
    )
    inlines = (ProfileInterestedJobsInline,)
    readonly_fields = (
        Profile.scores.field.name,
        Profile.score.field.name,
        Profile.credits.field.name,
        Profile.job_type.fget.__name__,
        Profile.job_location_type.fget.__name__,
    )

    exclude = (Profile.interested_jobs.field.name,)
    actions = ("recalculate_scores",)

    @admin.action(description="Recalculate Scores")
    def recalculate_scores(self, request, queryset):
        updated_profiles = []
        for profile in queryset:
            profile.scores = UserScorePack.calculate(profile.user)
            profile.score = sum(profile.scores.values())
            updated_profiles.append(profile)

        Profile.objects.bulk_update(updated_profiles, fields=[Profile.scores.field.name, Profile.score.field.name])


@register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = (Contact.contactable.field.name, Contact.type.field.name, Contact.value.field.name)
    search_fields = (
        fj(Contact.contactable, Profile.contactable.field.related_query_name(), Profile.user, User.email),
        Contact.type.field.name,
        Contact.value.field.name,
    )
    list_filter = (Contact.type.field.name,)
    raw_id_fields = (Contact.contactable.field.name,)


@register(Education)
class EducationAdmin(ExportMixin, admin.ModelAdmin):
    resource_classes = [EducationResource]
    list_display = (
        Education.user.field.name,
        Education.field.field.name,
        Education.degree.field.name,
        Education.start.field.name,
        Education.end.field.name,
        Education.status.field.name,
    )
    search_fields = (
        Education.degree.field.name,
        fj(Education.user, User.email),
        fj(Education.field, Field.name),
        fj(Education.city, City.name),
    )
    list_filter = (
        Education.degree.field.name,
        Education.status.field.name,
    )
    autocomplete_fields = (
        Education.user.field.name,
        Education.field.field.name,
        Education.university.field.name,
        Education.city.field.name,
    )


@register(IEEMethod)
class IEEMethodAdmin(admin.ModelAdmin):
    list_display = (
        IEEMethod.education.field.name,
        IEEMethod.education_evaluation_document.field.name,
        IEEMethod.evaluator.field.name,
    )
    search_fields = (
        fj(IEEMethod.education, Education.user, User.email),
        IEEMethod.evaluator.field.name,
    )
    list_filter = (IEEMethod.evaluator.field.name,)
    autocomplete_fields = (IEEMethod.education.field.name,)
    raw_id_fields = (IEEMethod.education_evaluation_document.field.name,)


@register(CommunicationMethod)
class CommunicationMethodAdmin(admin.ModelAdmin):
    list_display = (
        CommunicationMethod.education.field.name,
        CommunicationMethod.website.field.name,
        CommunicationMethod.email.field.name,
        CommunicationMethod.department.field.name,
        CommunicationMethod.person.field.name,
        CommunicationMethod.degree_file.field.name,
    )
    search_fields = (
        fj(CommunicationMethod.education, Education.user, User.email),
        CommunicationMethod.website.field.name,
        CommunicationMethod.email.field.name,
        CommunicationMethod.department.field.name,
        CommunicationMethod.person.field.name,
    )
    list_filter = (CommunicationMethod.department.field.name,)
    autocomplete_fields = (CommunicationMethod.education.field.name,)
    raw_id_fields = (CommunicationMethod.degree_file.field.name,)


@register(WorkExperience)
class WorkExperienceAdmin(ExportMixin, admin.ModelAdmin):
    resource_classes = [WorkExperienceResource]
    list_display = (
        WorkExperience.user.field.name,
        WorkExperience.job_title.field.name,
        WorkExperience.organization.field.name,
        WorkExperience.status.field.name,
        WorkExperience.start.field.name,
        WorkExperience.end.field.name,
    )
    search_fields = (
        fj(WorkExperience.user, User.email),
        WorkExperience.organization.field.name,
    )
    autocomplete_fields = (
        WorkExperience.user.field.name,
        WorkExperience.city.field.name,
    )


@register(EmployerLetterMethod)
class EmployerLetterMethodAdmin(admin.ModelAdmin):
    list_display = (
        EmployerLetterMethod.work_experience.field.name,
        EmployerLetterMethod.employer_letter.field.name,
        EmployerLetterMethod.verified_at.field.name,
        EmployerLetterMethod.created_at.field.name,
    )
    search_fields = (fj(EmployerLetterMethod.work_experience, WorkExperience.user, User.email),)
    raw_id_fields = (EmployerLetterMethod.employer_letter.field.name,)
    autocomplete_fields = (EmployerLetterMethod.work_experience.field.name,)


@register(PaystubsMethod)
class PaystubsMethodAdmin(admin.ModelAdmin):
    list_display = (
        PaystubsMethod.work_experience.field.name,
        PaystubsMethod.paystubs.field.name,
        PaystubsMethod.verified_at.field.name,
        PaystubsMethod.created_at.field.name,
    )
    search_fields = (fj(PaystubsMethod.work_experience, WorkExperience.user, User.email),)
    raw_id_fields = (PaystubsMethod.paystubs.field.name,)
    autocomplete_fields = (PaystubsMethod.work_experience.field.name,)


@register(ReferenceCheckEmployer)
class ReferenceCheckEmployerAdmin(admin.ModelAdmin):
    list_display = (
        ReferenceCheckEmployer.work_experience_verification.field.name,
        ReferenceCheckEmployer.name.field.name,
        ReferenceCheckEmployer.email.field.name,
        ReferenceCheckEmployer.phone_number.field.name,
        ReferenceCheckEmployer.position.field.name,
    )
    search_fields = (
        ReferenceCheckEmployer.email.field.name,
        ReferenceCheckEmployer.phone_number.field.name,
    )
    raw_id_fields = (ReferenceCheckEmployer.work_experience_verification.field.name,)


@register(LanguageCertificate)
class LanguageCertificateAdmin(ExportMixin, admin.ModelAdmin):
    resource_classes = [LanguageCertificateResource]
    list_display = (LanguageCertificate.user.field.name,)
    search_fields = (fj(LanguageCertificate.user, User.email),)
    autocomplete_fields = (LanguageCertificate.user.field.name,)


@register(LanguageCertificateValue)
class LanguageCertificateValueAdmin(admin.ModelAdmin):
    list_display = (
        fj(LanguageCertificateValue.language_certificate, LanguageCertificate.user, User.email),
        LanguageCertificateValue.skill.field.name,
        LanguageCertificateValue.value.field.name,
    )
    search_fields = (
        fj(LanguageCertificateValue.language_certificate, LanguageCertificate.user, User.email),
        LanguageCertificateValue.value.field.name,
    )
    autocomplete_fields = (LanguageCertificateValue.language_certificate.field.name,)


@register(CertificateAndLicense)
class CertificateAndLicenseAdmin(ExportMixin, admin.ModelAdmin):
    resource_classes = [CertificateAndLicenseResource]
    list_display = (
        CertificateAndLicense.user.field.name,
        CertificateAndLicense.title.field.name,
        CertificateAndLicense.certifier.field.name,
        CertificateAndLicense.status.field.name,
        CertificateAndLicense.issued_at.field.name,
        CertificateAndLicense.expired_at.field.name,
    )
    search_fields = (
        fj(CertificateAndLicense.user, User.email),
        CertificateAndLicense.title.field.name,
    )
    list_filter = (
        CertificateAndLicense.certifier.field.name,
        CertificateAndLicense.issued_at.field.name,
        CertificateAndLicense.expired_at.field.name,
    )
    autocomplete_fields = (CertificateAndLicense.user.field.name,)


@register(OfflineMethod)
class OfflineMethodAdmin(admin.ModelAdmin):
    list_display = (
        OfflineMethod.language_certificate.field.name,
        OfflineMethod.verified_at.field.name,
        OfflineMethod.created_at.field.name,
    )
    search_fields = (fj(OfflineMethod.language_certificate, LanguageCertificate.user, User.email),)
    list_filter = (
        OfflineMethod.verified_at.field.name,
        OfflineMethod.created_at.field.name,
    )
    autocomplete_fields = (OfflineMethod.language_certificate.field.name,)


@register(OnlineMethod)
class OnlineMethodAdmin(admin.ModelAdmin):
    list_display = (
        OnlineMethod.language_certificate.field.name,
        OnlineMethod.verified_at.field.name,
        OnlineMethod.created_at.field.name,
    )
    search_fields = (fj(OnlineMethod.language_certificate, LanguageCertificate.user, User.email),)
    list_filter = (
        OnlineMethod.verified_at.field.name,
        OnlineMethod.created_at.field.name,
    )
    autocomplete_fields = (OnlineMethod.language_certificate.field.name,)


@register(CertificateAndLicenseOfflineVerificationMethod)
class CertificateAndLicenseVerificationMethodAdmin(admin.ModelAdmin):
    @admin.action(description="Run Get Certificate Text Task")
    def run_get_certificate_text_task(
        self, request, queryset: QuerySet[CertificateAndLicenseOfflineVerificationMethod]
    ):
        for certificate_and_license_verification in queryset:
            user_task_runner(
                get_certificate_text,
                certificate_id=certificate_and_license_verification.certificate_and_license.pk,
                task_user_id=request.user.pk,
            )

    list_display = (
        CertificateAndLicenseOfflineVerificationMethod.certificate_and_license.field.name,
        CertificateAndLicenseOfflineVerificationMethod.verified_at.field.name,
        CertificateAndLicenseOfflineVerificationMethod.created_at.field.name,
    )
    search_fields = (
        fj(
            CertificateAndLicenseOfflineVerificationMethod.certificate_and_license,
            CertificateAndLicense.user,
            User.email,
        ),
    )
    list_filter = (
        CertificateAndLicenseOfflineVerificationMethod.verified_at.field.name,
        CertificateAndLicenseOfflineVerificationMethod.created_at.field.name,
    )
    autocomplete_fields = (CertificateAndLicenseOfflineVerificationMethod.certificate_and_license.field.name,)
    actions = (run_get_certificate_text_task.__name__,)


@register(CertificateAndLicenseOnlineVerificationMethod)
class CertificateAndLicenseOnlineVerificationMethodAdmin(admin.ModelAdmin):
    list_display = (
        CertificateAndLicenseOnlineVerificationMethod.certificate_and_license.field.name,
        CertificateAndLicenseOnlineVerificationMethod.verified_at.field.name,
        CertificateAndLicenseOnlineVerificationMethod.created_at.field.name,
    )
    search_fields = (
        fj(
            CertificateAndLicenseOnlineVerificationMethod.certificate_and_license,
            CertificateAndLicense.user,
            User.email,
        ),
    )
    list_filter = (
        CertificateAndLicenseOnlineVerificationMethod.verified_at.field.name,
        CertificateAndLicenseOnlineVerificationMethod.created_at.field.name,
    )
    autocomplete_fields = (CertificateAndLicenseOnlineVerificationMethod.certificate_and_license.field.name,)


@register(CanadaVisa)
class CanadaVisaAdmin(admin.ModelAdmin):
    list_display = (
        CanadaVisa.user.field.name,
        CanadaVisa.nationality.field.name,
        CanadaVisa.status.field.name,
    )
    search_fields = (
        fj(CanadaVisa.user, User.email),
        CanadaVisa.nationality.field.name,
    )
    list_filter = (CanadaVisa.status.field.name,)
    raw_id_fields = (CanadaVisa.citizenship_document.field.name,)
    autocomplete_fields = (
        CanadaVisa.user.field.name,
        CanadaVisa.nationality.field.name,
    )


@register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    @admin.action(description="Re-Evaluate Resume JSON")
    def reevaluate_resume_json(self, request, queryset: QuerySet[Resume]):
        for resume in queryset:
            set_user_resume_json(user_id=resume.user.pk)

    list_display = (
        Resume.user.field.name,
        Resume.file.field.name,
    )
    search_fields = (fj(Resume.user, User.email),)
    raw_id_fields = (Resume.file.field.name,)
    autocomplete_fields = (Resume.user.field.name,)
    actions = (reevaluate_resume_json.__name__,)


class ReferralUserInline(admin.TabularInline):
    model = ReferralUser
    extra = 1
    readonly_fields = (ReferralUser.referred_at.field.name,)
    autocomplete_fields = (ReferralUser.user.field.name,)


@register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = (
        Referral.user.field.name,
        Referral.code.field.name,
    )
    search_fields = (fj(Referral.user, User.email), Referral.code.field.name)
    autocomplete_fields = (Referral.user.field.name,)
    inlines = (ReferralUserInline,)


@register(SupportTicketCategory)
class SupportTicketCategoryAdmin(admin.ModelAdmin):
    list_display = (
        SupportTicketCategory.title.field.name,
        SupportTicketCategory.types.field.name,
    )
    search_fields = (SupportTicketCategory.title.field.name, SupportTicketCategory.types.field.name)


@register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = (
        SupportTicket.user.field.name,
        SupportTicket.title.field.name,
        SupportTicket.status.field.name,
        SupportTicket.category.field.name,
    )
    search_fields = (fj(SupportTicket.user, User.email), SupportTicket.title.field.name)
    list_filter = (SupportTicket.status.field.name, SupportTicket.category.field.name)
    autocomplete_fields = (SupportTicket.user.field.name,)


@register(UserTask)
class UserTaskAdmin(admin.ModelAdmin):
    list_display = (
        UserTask.user.field.name,
        UserTask.task_name.field.name,
        UserTask.status.field.name,
        UserTask.created.field.name,
        UserTask.modified.field.name,
    )
    search_fields = (fj(UserTask.user, User.email), UserTask.task_name.field.name)
    list_filter = (UserTask.status.field.name, UserTask.task_name.field.name)
    autocomplete_fields = (UserTask.user.field.name,)


class OrganizationRolesGenericInline(GenericStackedInline):
    model = Role
    ct_field = Role.managed_by_model.field.name
    ct_fk_field = Role.managed_by_id.field.name
    fields = (Role.slug.field.name, Role.title.field.name, Role.description.field.name)
    extra = 1


@register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    change_list_template = "admin/auth_account/organization/change_list.html"
    list_display = (
        Organization.name.field.name,
        Organization.user.field.name,
        Organization.type.field.name,
        Organization.city.field.name,
        Organization.verified_at.field.name,
    )
    search_fields = (
        Organization.name.field.name,
        Organization.short_name.field.name,
        Organization.national_number.field.name,
    )
    list_filter = (Organization.status.field.name,)
    raw_id_fields = (Organization.contactable.field.name,)
    autocomplete_fields = (
        Organization.industry.field.name,
        Organization.city.field.name,
        Organization.user.field.name,
    )
    inlines = (OrganizationRolesGenericInline,)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "create-organization/",
                self.admin_site.admin_view(self.create_organization_view),
                name="create-organization",
            ),
        ]
        return custom_urls + urls

    def create_organization_view(self, request):
        if request.method == "POST":
            form = OrganizationUserCreationForm(request.POST)
            if form.is_valid():
                organization: Organization = Organization.objects.create_organization(
                    form.cleaned_data["name"],
                    form.cleaned_data["website"],
                    email=form.cleaned_data["email"],
                    password=form.cleaned_data["password"],
                )
                organization.activate_login()

                self.message_user(
                    request,
                    _(f"Organization '{organization.name}' created successfully"),
                    level=messages.SUCCESS,
                )
                return HttpResponseRedirect(reverse("admin:auth_account_organization_change", args=[organization.pk]))
        else:
            form = OrganizationUserCreationForm()

        context = {
            "form": form,
            "opts": self.model._meta,
            "title": "Create Organization with User",
        }
        return render(request, "admin/auth_account/organization/create_organization.html", context)

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["create_organization_button"] = format_html(
            '<a href="{}" class="button addlink">Create Organization</a>', reverse("admin:create-organization")
        )

        return super().changelist_view(request, extra_context=extra_context)


@register(OrganizationMembership)
class OrganizationMembershipAdmin(admin.ModelAdmin):
    list_display = (
        OrganizationMembership.user.field.name,
        OrganizationMembership.organization.field.name,
        OrganizationMembership.role.field.name,
        OrganizationMembership.invited_by.field.name,
    )
    list_filter = (OrganizationMembership.role.field.name, OrganizationMembership.created_at.field.name)
    autocomplete_fields = (
        OrganizationMembership.organization.field.name,
        OrganizationMembership.user.field.name,
        OrganizationMembership.invited_by.field.name,
    )


@register(OrganizationInvitation)
class OrganizationInvitationAdmin(admin.ModelAdmin):
    list_display = (
        OrganizationInvitation.organization.field.name,
        OrganizationInvitation.email.field.name,
        OrganizationInvitation.role.field.name,
        OrganizationInvitation.created_at.field.name,
        OrganizationInvitation.created_by.field.name,
    )
    autocomplete_fields = (
        OrganizationInvitation.organization.field.name,
        OrganizationInvitation.created_by.field.name,
    )
    search_fields = (
        OrganizationInvitation.email.field.name,
        OrganizationInvitation.organization.field.name,
    )
    list_filter = (
        OrganizationInvitation.role.field.name,
        OrganizationInvitation.created_at.field.name,
    )


@register(Contactable)
class ContactableAdmin(admin.ModelAdmin):
    list_display = (
        Contactable.id.field.name,
        *Contactable.get_contactable_model_related_fields().values(),
        "contacts_count",
    )
    readonly_fields = (*Contactable.get_contactable_model_related_fields().values(),)
    search_fields = ("pk",)

    def get_search_fields(self, request):
        related_fields = Contactable.get_contactable_model_related_fields()
        return list(super().get_search_fields(request)) + [
            fj(related_fields[field], f)
            for field in Contactable.get_contactable_model_fields()
            for f in admin.site._registry[field.field.model].get_search_fields(request)
        ]

    @admin.display(description="Contacts Count")
    def contacts_count(self, obj):
        return obj.contacts.count()


@register(DNSTXTRecordMethod)
class DNSTXTRecordMethodAdmin(admin.ModelAdmin):
    list_display = (
        DNSTXTRecordMethod.code.field.name,
        DNSTXTRecordMethod.organization.field.name,
        DNSTXTRecordMethod.verified_at.field.name,
        DNSTXTRecordMethod.created_at.field.name,
    )
    search_fields = (DNSTXTRecordMethod.organization.field.name,)
    list_filter = (
        DNSTXTRecordMethod.verified_at.field.name,
        DNSTXTRecordMethod.created_at.field.name,
    )
    autocomplete_fields = (DNSTXTRecordMethod.organization.field.name,)


@register(UploadFileToWebsiteMethod)
class UploadFileToWebsiteMethodAdmin(admin.ModelAdmin):
    list_display = (
        UploadFileToWebsiteMethod.file_name.field.name,
        UploadFileToWebsiteMethod.organization.field.name,
        UploadFileToWebsiteMethod.verified_at.field.name,
        UploadFileToWebsiteMethod.created_at.field.name,
    )
    search_fields = (UploadFileToWebsiteMethod.organization.field.name,)
    list_filter = (
        UploadFileToWebsiteMethod.verified_at.field.name,
        UploadFileToWebsiteMethod.created_at.field.name,
    )
    autocomplete_fields = (UploadFileToWebsiteMethod.organization.field.name,)


@register(CommunicateOrganizationMethod)
class CommunicateOrganizationMethodAdmin(admin.ModelAdmin):
    list_display = (
        CommunicateOrganizationMethod.organization.field.name,
        CommunicateOrganizationMethod.verified_at.field.name,
        CommunicateOrganizationMethod.created_at.field.name,
    )
    search_fields = (CommunicateOrganizationMethod.organization.field.name,)
    list_filter = (
        CommunicateOrganizationMethod.verified_at.field.name,
        CommunicateOrganizationMethod.created_at.field.name,
    )
    autocomplete_fields = (CommunicateOrganizationMethod.organization.field.name,)
    readonly_fields = (CommunicateOrganizationMethod.get_otp.__name__,)


@register(UploadCompanyCertificateMethod)
class UploadCompanyCertificateMethodAdmin(admin.ModelAdmin):
    list_display = (
        UploadCompanyCertificateMethod.organization.field.name,
        UploadCompanyCertificateMethod.verified_at.field.name,
        UploadCompanyCertificateMethod.created_at.field.name,
    )
    search_fields = (UploadCompanyCertificateMethod.organization.field.name,)
    list_filter = (
        UploadCompanyCertificateMethod.verified_at.field.name,
        UploadCompanyCertificateMethod.created_at.field.name,
    )
    raw_id_fields = (UploadCompanyCertificateMethod.organization_certificate_file.field.name,)
    autocomplete_fields = (UploadCompanyCertificateMethod.organization.field.name,)


@register(OrganizationJobPosition)
class OrganizationJobPositionAdmin(admin.ModelAdmin):
    list_display = (
        OrganizationJobPosition.title.field.name,
        OrganizationJobPosition.status.field.name,
        OrganizationJobPosition.organization.field.name,
        OrganizationJobPosition.validity_date.field.name,
        OrganizationJobPosition.created_at.field.name,
    )
    search_fields = (
        OrganizationJobPosition.title.field.name,
        fj(OrganizationJobPosition.organization, Organization.name),
    )
    list_filter = (
        OrganizationJobPosition.status.field.name,
        OrganizationJobPosition.age_range.field.name,
        OrganizationJobPosition.contract_type.field.name,
        OrganizationJobPosition.location_type.field.name,
        OrganizationJobPosition.payment_term.field.name,
        OrganizationJobPosition.start_at.field.name,
        OrganizationJobPosition.validity_date.field.name,
        OrganizationJobPosition.created_at.field.name,
    )
    autocomplete_fields = (
        OrganizationJobPosition.organization.field.name,
        OrganizationJobPosition.skills.field.name,
        OrganizationJobPosition.fields.field.name,
        OrganizationJobPosition.city.field.name,
    )


@register(OrganizationJobPositionStatusHistory)
class OrganizationJobPositionStatusHistoryAdmin(admin.ModelAdmin):
    list_display = (
        OrganizationJobPositionStatusHistory.job_position.field.name,
        OrganizationJobPositionStatusHistory.status.field.name,
        OrganizationJobPositionStatusHistory.created_at.field.name,
    )
    list_filter = (
        OrganizationJobPositionStatusHistory.status.field.name,
        OrganizationJobPositionStatusHistory.created_at.field.name,
    )
    autocomplete_fields = (OrganizationJobPositionStatusHistory.job_position.field.name,)


@register(JobPositionAssignment)
class JobPositionAssignmentAdmin(admin.ModelAdmin):
    list_display = (
        JobPositionAssignment.job_seeker.field.name,
        JobPositionAssignment.job_position.field.name,
        JobPositionAssignment.status.field.name,
        JobPositionAssignment.created_at.field.name,
    )
    search_fields = (
        fj(JobPositionAssignment.job_seeker, User.email),
        fj(JobPositionAssignment.job_position, OrganizationJobPosition.title),
    )
    autocomplete_fields = (JobPositionAssignment.job_position.field.name, JobPositionAssignment.job_seeker.field.name)


@register(JobPositionAssignmentStatusHistory)
class JobPositionAssignmentStatusHistoryAdmin(admin.ModelAdmin):
    list_display = (
        JobPositionAssignmentStatusHistory.job_position_assignment.field.name,
        JobPositionAssignmentStatusHistory.status.field.name,
        JobPositionAssignmentStatusHistory.created_at.field.name,
    )
    list_filter = (
        JobPositionAssignmentStatusHistory.status.field.name,
        JobPositionAssignmentStatusHistory.created_at.field.name,
    )
    search_fields = (
        fj(
            JobPositionAssignmentStatusHistory.job_position_assignment,
            JobPositionAssignment.job_seeker,
            User.email,
        ),
        fj(
            JobPositionAssignmentStatusHistory.job_position_assignment,
            JobPositionAssignment.job_position,
            OrganizationJobPosition.title,
        ),
    )
    autocomplete_fields = (JobPositionAssignmentStatusHistory.job_position_assignment.field.name,)


@register(JobPositionInterview)
class JobPositionInterviewAdmin(admin.ModelAdmin):
    list_display = (
        JobPositionInterview.job_position_assignment.field.name,
        JobPositionInterview.interview_date.field.name,
        JobPositionInterview.result_date.field.name,
        JobPositionInterview.created_at.field.name,
    )
    list_filter = (
        JobPositionInterview.interview_date.field.name,
        JobPositionInterview.result_date.field.name,
        JobPositionInterview.created_at.field.name,
    )
    autocomplete_fields = (
        JobPositionInterview.job_position_assignment.field.name,
        JobPositionInterview.assignment_status_history.field.name,
    )


@register(OrganizationEmployee)
class OrganizationEmployeeAdmin(admin.ModelAdmin):
    list_display = (
        OrganizationEmployee.user.field.name,
        OrganizationEmployee.organization.field.name,
        OrganizationEmployee.created.field.name,
    )
    search_fields = (
        fj(OrganizationEmployee.user, User.email),
        fj(OrganizationEmployee.organization, Organization.name),
    )
    list_filter = (OrganizationEmployee.created.field.name,)
    autocomplete_fields = (OrganizationEmployee.user.field.name, OrganizationEmployee.organization.field.name)


@register(OrganizationPlatformMessage)
class OrganizationPlatformMessageAdmin(admin.ModelAdmin):
    list_display = (
        OrganizationPlatformMessage.assignee_type.field.name,
        OrganizationPlatformMessage.source.field.name,
        OrganizationPlatformMessage.title.field.name,
        OrganizationPlatformMessage.organization_employee_cooperation.field.name,
        OrganizationPlatformMessage.read_at.field.name,
        OrganizationPlatformMessage.created.field.name,
    )
    search_fields = (OrganizationPlatformMessage.title.field.name,)
    list_filter = (
        OrganizationPlatformMessage.assignee_type.field.name,
        OrganizationPlatformMessage.created.field.name,
        OrganizationPlatformMessage.read_at.field.name,
    )
    autocomplete_fields = (OrganizationPlatformMessage.organization_employee_cooperation.field.name,)


@register(OrganizationPlatformMessageAttachment)
class OrganizationPlatformMessageAttachmentAdmin(admin.ModelAdmin):
    list_display = (
        OrganizationPlatformMessageAttachment.organization_platform_message.field.name,
        OrganizationPlatformMessageAttachment.text.field.name,
    )
    search_fields = (OrganizationPlatformMessageAttachment.text.field.name,)
    autocomplete_fields = (OrganizationPlatformMessageAttachment.organization_platform_message.field.name,)


@register(PlatformMessageAttachmentFile)
class PlatformMessageAttachmentFileAdmin(admin.ModelAdmin):
    list_display = (
        PlatformMessageAttachmentFile.text.field.name,
        PlatformMessageAttachmentFile.file.field.name,
        PlatformMessageAttachmentFile.organization_platform_message.field.name,
    )
    raw_id_fields = (PlatformMessageAttachmentFile.file.field.name,)

    autocomplete_fields = (PlatformMessageAttachmentFile.organization_platform_message.field.name,)


@register(PlatformMessageAttachmentCourse)
class PlatformMessageAttachmentCourseAdmin(admin.ModelAdmin):
    list_display = (
        PlatformMessageAttachmentCourse.text.field.name,
        PlatformMessageAttachmentCourse.organization_platform_message.field.name,
        PlatformMessageAttachmentCourse.course.field.name,
    )
    search_fields = (
        fj(PlatformMessageAttachmentCourse.course, Course.name),
        fj(PlatformMessageAttachmentCourse.course, Course.external_id),
    )
    autocomplete_fields = (
        PlatformMessageAttachmentCourse.course.field.name,
        PlatformMessageAttachmentCourse.organization_platform_message.field.name,
    )


@register(PlatformMessageAttachmentCourseResult)
class PlatformMessageAttachmentCourseResultAdmin(admin.ModelAdmin):
    list_display = (
        PlatformMessageAttachmentCourseResult.text.field.name,
        PlatformMessageAttachmentCourseResult.course_result.field.name,
        PlatformMessageAttachmentCourseResult.organization_platform_message.field.name,
    )
    search_fields = (
        fj(PlatformMessageAttachmentCourseResult.course_result, CourseResult.course, Course.name),
        fj(PlatformMessageAttachmentCourseResult.course_result, CourseResult.user, User.email),
    )
    autocomplete_fields = (
        PlatformMessageAttachmentCourseResult.course_result.field.name,
        PlatformMessageAttachmentCourseResult.organization_platform_message.field.name,
    )


@register(OrganizationEmployeeCooperation)
class OrganizationEmployeeCooperationAdmin(admin.ModelAdmin):
    list_display = (
        OrganizationEmployeeCooperation.employee.field.name,
        OrganizationEmployeeCooperation.status.field.name,
        OrganizationEmployeeCooperation.job_position_assignment.field.name,
        OrganizationEmployeeCooperation.start_at.field.name,
        OrganizationEmployeeCooperation.end_at.field.name,
        OrganizationEmployeeCooperation.created_at.field.name,
    )
    search_fields = (
        fj(
            OrganizationEmployeeCooperation.employee,
            OrganizationEmployee.user,
            User.email,
        ),
        fj(
            OrganizationEmployeeCooperation.employee,
            OrganizationEmployee.organization,
            Organization.name,
        ),
        fj(
            OrganizationEmployeeCooperation.job_position_assignment,
            JobPositionAssignment.job_position,
            OrganizationJobPosition.title,
        ),
    )
    list_filter = (
        OrganizationEmployeeCooperation.created_at.field.name,
        OrganizationEmployeeCooperation.status.field.name,
        OrganizationEmployeeCooperation.start_at.field.name,
        OrganizationEmployeeCooperation.end_at.field.name,
    )
    autocomplete_fields = (
        OrganizationEmployeeCooperation.employee.field.name,
        OrganizationEmployeeCooperation.job_position_assignment.field.name,
    )


@register(OrganizationEmployeeCooperationStatusHistory)
class OrganizationEmployeeHiringStatusHistoryAdmin(admin.ModelAdmin):
    list_display = (
        OrganizationEmployeeCooperationStatusHistory.organization_employee_cooperation.field.name,
        OrganizationEmployeeCooperationStatusHistory.status.field.name,
        OrganizationEmployeeCooperationStatusHistory.created_at.field.name,
    )
    list_filter = (
        OrganizationEmployeeCooperationStatusHistory.status.field.name,
        OrganizationEmployeeCooperationStatusHistory.created_at.field.name,
    )
    autocomplete_fields = (OrganizationEmployeeCooperationStatusHistory.organization_employee_cooperation.field.name,)


@register(OrganizationEmployeePerformanceReport)
class OrganizationEmployeePerformanceReportAdmin(admin.ModelAdmin):
    list_display = (
        OrganizationEmployeePerformanceReport.status.field.name,
        OrganizationEmployeePerformanceReport.organization_employee_cooperation.field.name,
        OrganizationEmployeePerformanceReport.title.field.name,
        OrganizationEmployeePerformanceReport.date.field.name,
        OrganizationEmployeePerformanceReport.created.field.name,
    )
    search_fields = (
        fj(
            OrganizationEmployeePerformanceReport.organization_employee_cooperation,
            OrganizationEmployeeCooperation.employee,
            User.email,
        ),
    )
    list_filter = (
        OrganizationEmployeePerformanceReport.date.field.name,
        OrganizationEmployeePerformanceReport.status.field.name,
        OrganizationEmployeePerformanceReport.created.field.name,
    )
    autocomplete_fields = (OrganizationEmployeePerformanceReport.organization_employee_cooperation.field.name,)


@register(PerformanceReportQuestion)
class PerformanceReportQuestionAdmin(admin.ModelAdmin):
    list_display = (
        PerformanceReportQuestion.title.field.name,
        PerformanceReportQuestion.type.field.name,
        PerformanceReportQuestion.weight.field.name,
    )
    search_fields = (PerformanceReportQuestion.title.field.name,)
    list_filter = (PerformanceReportQuestion.type.field.name,)


@register(PerformanceReportAnswer)
class PerformanceReportAnswerAdmin(admin.ModelAdmin):
    list_display = (
        PerformanceReportAnswer.organization_employee_performance_report.field.name,
        PerformanceReportAnswer.question.field.name,
        PerformanceReportAnswer.respondent.field.name,
    )
    search_fields = (PerformanceReportAnswer.question.field.name,)
    list_filter = (PerformanceReportAnswer.respondent.field.name,)
    autocomplete_fields = (
        PerformanceReportAnswer.organization_employee_performance_report.field.name,
        PerformanceReportAnswer.question.field.name,
    )


@register(OrganizationEmployeePerformanceReportStatusHistory)
class OrganizationEmployeePerformanceReportStatusHistoryAdmin(admin.ModelAdmin):
    list_display = (
        OrganizationEmployeePerformanceReportStatusHistory.organization_employee_performance_report.field.name,
        OrganizationEmployeePerformanceReportStatusHistory.status.field.name,
        OrganizationEmployeePerformanceReportStatusHistory.created_at.field.name,
    )
    list_filter = (
        OrganizationEmployeePerformanceReportStatusHistory.status.field.name,
        OrganizationEmployeePerformanceReportStatusHistory.created_at.field.name,
    )
    autocomplete_fields = (
        OrganizationEmployeePerformanceReportStatusHistory.organization_employee_performance_report.field.name,
    )
