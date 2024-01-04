from graphql_auth.models import UserStatus

from django.contrib import admin
from django.contrib.admin import register
from django.contrib.auth.admin import UserAdmin as UserAdminBase
from django.utils.translation import gettext_lazy as _

from .forms import UserChangeForm
from .models import (
    CertificateAndLicense,
    CommunicationMethod,
    Contact,
    Education,
    IEEMethod,
    LanguageCertificate,
    Profile,
    User,
    WorkExperience,
    EmployerLetterMethod,
    PaystubsMethod,
    ReferenceCheckEmployer,
    OfflineMethod,
    OnlineMethod,
    CertificateAndLicenseOfflineVerificationMethod,
    CertificateAndLicenseOnlineVerificationMethod,
    CanadaVisa,
    JobAssessmentResult,
)


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
    )

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
                    User.gender.field.name,
                    User.birth_date.field.name,
                    User.raw_skills.field.name,
                    User.available_jobs.field.name,
                )
            },
        )
        self.fieldsets = tuple(fieldsets)


@register(UserStatus)
class UserStatusAdmin(admin.ModelAdmin):
    list_display = ("user", "verified", "archived", "secondary_email")
    search_fields = ("user__email",)
    list_filter = ("verified", "archived")
    raw_id_fields = ("user",)


@register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "height", "weight", "skin_color", "hair_color", "eye_color")
    search_fields = ("user__email", "job__name")
    list_filter = ("skin_color", "eye_color")
    raw_id_fields = ("user", "interested_jobs", "city")


@register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ("user", "type", "value")
    search_fields = ("user__email", "type", "value")
    list_filter = ("type",)
    raw_id_fields = ("user",)


@register(Education)
class EducationAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "field", "degree", "start", "end", "status")
    search_fields = ("user__email", "field__name", "degree", "city__name")
    list_filter = ("degree", "status")
    raw_id_fields = ("user", "field")


@register(IEEMethod)
class IEEMethodAdmin(admin.ModelAdmin):
    list_display = ("education", "ices_document", "citizen_document", "evaluator")
    search_fields = ("education__user__email", "evaluator")
    list_filter = ("evaluator",)
    raw_id_fields = ("education",)


@register(CommunicationMethod)
class CommunicationMethodAdmin(admin.ModelAdmin):
    list_display = ("education", "email", "department", "person", "degree_file")
    search_fields = ("education__user__email", "email", "department", "person")
    list_filter = ("department",)
    raw_id_fields = ("education",)


@register(WorkExperience)
class WorkExperienceAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "job", "organization", "status", "start", "end")
    search_fields = (
        "user__email",
        "organization",
    )
    raw_id_fields = (
        "user",
        "city",
    )


@register(EmployerLetterMethod)
class EmployerLetterMethodAdmin(admin.ModelAdmin):
    list_display = (
        "work_experience",
        "employer_letter",
        "verified_at",
        "created_at",
    )
    search_fields = ("work_experience__user__email",)
    list_filter = (
        "verified_at",
        "created_at",
    )
    raw_id_fields = ("work_experience",)


@register(PaystubsMethod)
class PaystubsMethodAdmin(admin.ModelAdmin):
    list_display = (
        "work_experience",
        "paystubs",
        "verified_at",
        "created_at",
    )
    search_fields = ("work_experience__user__email",)
    list_filter = (
        "verified_at",
        "created_at",
    )
    raw_id_fields = ("work_experience",)


@register(ReferenceCheckEmployer)
class ReferenceCheckEmployerAdmin(admin.ModelAdmin):
    list_display = ("work_experience_verification", "name", "email", "phone_number", "position")
    search_fields = (
        "email",
        "phone_number",
    )
    raw_id_fields = ("work_experience_verification",)


@register(LanguageCertificate)
class LanguageCertificateAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "language__code", "test__title", "status", "issued_at", "expired_at", "band_score")
    search_fields = (
        "user__email",
        "language__code",
    )
    list_filter = ("language__code", "test__title", "issued_at", "expired_at")
    raw_id_fields = ("user", "language", "test")


@register(CertificateAndLicense)
class CertificateAndLicenseAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "title", "certifier", "status", "issued_at", "expired_at")
    search_fields = ("user__email", "title")
    list_filter = ("certifier", "issued_at", "expired_at")
    raw_id_fields = ("user",)


@register(OfflineMethod)
class OfflineMethodAdmin(admin.ModelAdmin):
    list_display = ("language_certificate", "verified_at", "created_at")
    search_fields = ("language_certificate__user__email",)
    list_filter = ("verified_at", "created_at")
    raw_id_fields = ("language_certificate",)


@register(OnlineMethod)
class OnlineMethodAdmin(admin.ModelAdmin):
    list_display = ("language_certificate", "verified_at", "created_at")
    search_fields = ("language_certificate__user__email",)
    list_filter = ("verified_at", "created_at")
    raw_id_fields = ("language_certificate",)


@register(CertificateAndLicenseOfflineVerificationMethod)
class CertificateAndLicenseVerificationMethodAdmin(admin.ModelAdmin):
    list_display = ("certificate_and_license", "verified_at", "created_at")
    search_fields = ("certificate_and_license__user__email",)
    list_filter = ("verified_at", "created_at")
    raw_id_fields = ("certificate_and_license",)


@register(CertificateAndLicenseOnlineVerificationMethod)
class CertificateAndLicenseOnlineVerificationMethodAdmin(admin.ModelAdmin):
    list_display = ("certificate_and_license", "verified_at", "created_at")
    search_fields = ("certificate_and_license__user__email",)
    list_filter = ("verified_at", "created_at")
    raw_id_fields = ("certificate_and_license",)


@register(CanadaVisa)
class CanadaVisaAdmin(admin.ModelAdmin):
    list_display = ("user", "nationality", "status",)
    search_fields = ("user__email", "nationality")
    list_filter = ("status",)
    raw_id_fields = ("user", "nationality",)


@register(JobAssessmentResult)
class JobAssessmentResultAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "job_assessment",
        "score",
        "status",
        "created_at",
        "updated_at",
    )
    search_fields = (
        "user__email",
        "job_assessment__title",
    )
    list_filter = (
        "status",
        "created_at",
        "updated_at",
    )
    raw_id_fields = (
        "user",
        "job_assessment",
    )
