from cities_light.models import City
from common.models import Field
from common.utils import fields_join
from graphql_auth.models import UserStatus

from django.contrib import admin
from django.contrib.admin import register
from django.contrib.auth.admin import UserAdmin as UserAdminBase
from django.utils.translation import gettext_lazy as _

from .forms import UserChangeForm
from .models import (
    AvatarFile,
    CanadaVisa,
    CertificateAndLicense,
    CertificateAndLicenseOfflineVerificationMethod,
    CertificateAndLicenseOnlineVerificationMethod,
    CommunicationMethod,
    Contact,
    Education,
    EmployerLetterMethod,
    IEEMethod,
    LanguageCertificate,
    LanguageCertificateValue,
    OfflineMethod,
    OnlineMethod,
    PaystubsMethod,
    Profile,
    ReferenceCheckEmployer,
    Referral,
    ReferralUser,
    Resume,
    User,
    WorkExperience,
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
    readonly_fields = (User.skills.field.name,)

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
                    User.skills.field.name,
                    User.available_jobs.field.name,
                )
            },
        )
        self.fieldsets = tuple(fieldsets)


@register(UserStatus)
class UserStatusAdmin(admin.ModelAdmin):
    list_display = (
        UserStatus.user.field.name,
        UserStatus.verified.field.name,
        UserStatus.archived.field.name,
        UserStatus.secondary_email.field.name,
    )
    search_fields = (fields_join(UserStatus.user, User.email),)
    list_filter = (
        UserStatus.verified.field.name,
        UserStatus.archived.field.name,
    )
    raw_id_fields = (UserStatus.user.field.name,)


class ProfileInterestedJobsInline(admin.TabularInline):
    model = Profile.interested_jobs.through
    extra = 1
    raw_id_fields = (Profile.interested_jobs.through.job.field.name,)


@register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        Profile.user.field.name,
        Profile.height.field.name,
        Profile.weight.field.name,
        Profile.skin_color.field.name,
        Profile.hair_color.field.name,
        Profile.eye_color.field.name,
    )
    search_fields = (fields_join(Profile.user, User.email),)
    list_filter = (
        Profile.height.field.name,
        Profile.weight.field.name,
        Profile.skin_color.field.name,
        Profile.hair_color.field.name,
    )
    raw_id_fields = (
        Profile.user.field.name,
        Profile.city.field.name,
        Profile.job_city.field.name,
    )
    inlines = (ProfileInterestedJobsInline,)
    readonly_fields = (Profile.credits.field.name,)
    exclude = (Profile.interested_jobs.field.name,)


@register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = (Contact.user.field.name, Contact.type.field.name, Contact.value.field.name)
    search_fields = (fields_join(Contact.user, User.email), Contact.type.field.name, Contact.value.field.name)
    list_filter = (Contact.type.field.name,)
    raw_id_fields = (Contact.user.field.name,)


@register(Education)
class EducationAdmin(admin.ModelAdmin):
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
        fields_join(Education.user, User.email),
        fields_join(Education.field, Field.name),
        fields_join(Education.city, City.name),
    )
    list_filter = (
        Education.degree.field.name,
        Education.status.field.name,
    )
    raw_id_fields = (
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
        fields_join(IEEMethod.education, Education.user, User.email),
        IEEMethod.evaluator.field.name,
    )
    list_filter = (IEEMethod.evaluator.field.name,)
    raw_id_fields = (IEEMethod.education.field.name,)


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
        fields_join(CommunicationMethod.education, Education.user, User.email),
        CommunicationMethod.website.field.name,
        CommunicationMethod.email.field.name,
        CommunicationMethod.department.field.name,
        CommunicationMethod.person.field.name,
    )
    list_filter = (CommunicationMethod.department.field.name,)
    raw_id_fields = (CommunicationMethod.education.field.name,)


@register(WorkExperience)
class WorkExperienceAdmin(admin.ModelAdmin):
    list_display = (
        WorkExperience.user.field.name,
        WorkExperience.job.field.name,
        WorkExperience.organization.field.name,
        WorkExperience.status.field.name,
        WorkExperience.start.field.name,
        WorkExperience.end.field.name,
    )
    search_fields = (
        fields_join(WorkExperience.user, User.email),
        WorkExperience.organization.field.name,
    )
    raw_id_fields = (
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
    search_fields = (fields_join(EmployerLetterMethod.work_experience, WorkExperience.user, User.email),)
    raw_id_fields = (EmployerLetterMethod.work_experience.field.name,)


@register(PaystubsMethod)
class PaystubsMethodAdmin(admin.ModelAdmin):
    list_display = (
        PaystubsMethod.work_experience.field.name,
        PaystubsMethod.paystubs.field.name,
        PaystubsMethod.verified_at.field.name,
        PaystubsMethod.created_at.field.name,
    )
    search_fields = (fields_join(PaystubsMethod.work_experience, WorkExperience.user, User.email),)
    raw_id_fields = (PaystubsMethod.work_experience.field.name,)


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
class LanguageCertificateAdmin(admin.ModelAdmin):
    list_display = (LanguageCertificate.user.field.name,)
    search_fields = (fields_join(LanguageCertificate.user, User.email),)
    raw_id_fields = (LanguageCertificate.user.field.name,)


@register(LanguageCertificateValue)
class LanguageCertificateValueAdmin(admin.ModelAdmin):
    list_display = (
        fields_join(LanguageCertificateValue.language_certificate, LanguageCertificate.user, User.email),
        LanguageCertificateValue.skill.field.name,
        LanguageCertificateValue.value.field.name,
    )
    search_fields = (
        fields_join(LanguageCertificateValue.language_certificate, LanguageCertificate.user, User.email),
        LanguageCertificateValue.value.field.name,
    )
    raw_id_fields = (LanguageCertificateValue.language_certificate.field.name,)


@register(CertificateAndLicense)
class CertificateAndLicenseAdmin(admin.ModelAdmin):
    list_display = (
        CertificateAndLicense.user.field.name,
        CertificateAndLicense.title.field.name,
        CertificateAndLicense.certifier.field.name,
        CertificateAndLicense.status.field.name,
        CertificateAndLicense.issued_at.field.name,
        CertificateAndLicense.expired_at.field.name,
    )
    search_fields = (
        fields_join(CertificateAndLicense.user, User.email),
        CertificateAndLicense.title.field.name,
    )
    list_filter = (
        CertificateAndLicense.certifier.field.name,
        CertificateAndLicense.issued_at.field.name,
        CertificateAndLicense.expired_at.field.name,
    )
    raw_id_fields = (CertificateAndLicense.user.field.name,)


@register(OfflineMethod)
class OfflineMethodAdmin(admin.ModelAdmin):
    list_display = (
        OfflineMethod.language_certificate.field.name,
        OfflineMethod.verified_at.field.name,
        OfflineMethod.created_at.field.name,
    )
    search_fields = (fields_join(OfflineMethod.language_certificate, LanguageCertificate.user, User.email),)
    list_filter = (
        OfflineMethod.verified_at.field.name,
        OfflineMethod.created_at.field.name,
    )
    raw_id_fields = (OfflineMethod.language_certificate.field.name,)


@register(OnlineMethod)
class OnlineMethodAdmin(admin.ModelAdmin):
    list_display = (
        OnlineMethod.language_certificate.field.name,
        OnlineMethod.verified_at.field.name,
        OnlineMethod.created_at.field.name,
    )
    search_fields = (fields_join(OnlineMethod.language_certificate, LanguageCertificate.user, User.email),)
    list_filter = (
        OnlineMethod.verified_at.field.name,
        OnlineMethod.created_at.field.name,
    )
    raw_id_fields = (OnlineMethod.language_certificate.field.name,)


@register(CertificateAndLicenseOfflineVerificationMethod)
class CertificateAndLicenseVerificationMethodAdmin(admin.ModelAdmin):
    list_display = (
        CertificateAndLicenseOfflineVerificationMethod.certificate_and_license.field.name,
        CertificateAndLicenseOfflineVerificationMethod.verified_at.field.name,
        CertificateAndLicenseOfflineVerificationMethod.created_at.field.name,
    )
    search_fields = (
        fields_join(
            CertificateAndLicenseOfflineVerificationMethod.certificate_and_license,
            CertificateAndLicense.user,
            User.email,
        ),
    )
    list_filter = (
        CertificateAndLicenseOfflineVerificationMethod.verified_at.field.name,
        CertificateAndLicenseOfflineVerificationMethod.created_at.field.name,
    )
    raw_id_fields = (CertificateAndLicenseOfflineVerificationMethod.certificate_and_license.field.name,)


@register(CertificateAndLicenseOnlineVerificationMethod)
class CertificateAndLicenseOnlineVerificationMethodAdmin(admin.ModelAdmin):
    list_display = (
        CertificateAndLicenseOnlineVerificationMethod.certificate_and_license.field.name,
        CertificateAndLicenseOnlineVerificationMethod.verified_at.field.name,
        CertificateAndLicenseOnlineVerificationMethod.created_at.field.name,
    )
    search_fields = (
        fields_join(
            CertificateAndLicenseOnlineVerificationMethod.certificate_and_license,
            CertificateAndLicense.user,
            User.email,
        ),
    )
    list_filter = (
        CertificateAndLicenseOnlineVerificationMethod.verified_at.field.name,
        CertificateAndLicenseOnlineVerificationMethod.created_at.field.name,
    )
    raw_id_fields = (CertificateAndLicenseOnlineVerificationMethod.certificate_and_license.field.name,)


@register(CanadaVisa)
class CanadaVisaAdmin(admin.ModelAdmin):
    list_display = (
        CanadaVisa.user.field.name,
        CanadaVisa.nationality.field.name,
        CanadaVisa.status.field.name,
    )
    search_fields = (
        fields_join(CanadaVisa.user, User.email),
        CanadaVisa.nationality.field.name,
    )
    list_filter = (CanadaVisa.status.field.name,)
    raw_id_fields = (
        CanadaVisa.user.field.name,
        CanadaVisa.nationality.field.name,
    )


@register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = (
        Resume.user.field.name,
        Resume.file.field.name,
    )
    search_fields = (fields_join(Resume.user, User.email), Resume.file.field.name)
    raw_id_fields = (Resume.user.field.name,)


class ReferralUserInline(admin.TabularInline):
    model = ReferralUser
    extra = 1
    readonly_fields = (ReferralUser.referred_at.field.name,)
    raw_id_fields = (ReferralUser.user.field.name,)


@register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = (
        Referral.user.field.name,
        Referral.code.field.name,
    )
    search_fields = (fields_join(Referral.user, User.email), Referral.code.field.name)
    raw_id_fields = (Referral.user.field.name,)
    inlines = (ReferralUserInline,)


@register(AvatarFile)
class AvatarFileAdmin(admin.ModelAdmin):
    list_display = (
        AvatarFile.uploaded_by.field.name,
        AvatarFile.file.field.name,
    )
    search_fields = (fields_join(AvatarFile.uploaded_by, User.email), AvatarFile.file.field.name)
    raw_id_fields = (AvatarFile.uploaded_by.field.name,)
