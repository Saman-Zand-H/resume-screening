from graphql_auth.models import UserStatus

from django.contrib import admin
from django.contrib.admin import register
from django.contrib.auth.admin import UserAdmin as UserAdminBase
from django.utils.translation import gettext_lazy as _

from .forms import UserChangeForm
from .models import (
    CommunicationMethod,
    Contact,
    Education,
    IEEMethod,
    Profile,
    User,
    WorkExperience,
    LanguageCertificate,
    CertificateAndLicense,
    UserSkill,
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
    list_display = ("user", "field", "degree", "start", "end", "status")
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


@register(LanguageCertificate)
class LanguageCertificateAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "language__code", "test__title", "issued_at", "expired_at", "band_score")
    search_fields = (
        "user__email",
        "language__code",
    )
    list_filter = ("language__code", "test__title", "issued_at", "expired_at")
    raw_id_fields = ("user", "language", "test")


@register(CertificateAndLicense)
class CertificateAndLicenseAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "title", "certifier", "issued_at", "expired_at")
    search_fields = ("user__email", "title")
    list_filter = ("certifier", "issued_at", "expired_at")
    raw_id_fields = ("user",)


@register(UserSkill)
class UserSkillAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "get_skills",
    )
    search_fields = ("user__email",)
    raw_id_fields = ("user", "skills")

    def get_skills(self, obj):
        return ", ".join([skill.title for skill in obj.skills.all()])

    get_skills.short_description = "Skills"
