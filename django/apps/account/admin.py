from graphql_auth.models import UserStatus

from django.contrib import admin
from django.contrib.admin import register
from django.contrib.auth.admin import UserAdmin as UserAdminBase
from django.utils.translation import gettext_lazy as _

from .forms import UserChangeForm
from .models import (
    CommunicationMethod,
    Education,
    EducationVerification,
    IEEMethod,
    User,
    UserProfile,
)


@register(User)
class UserAdmin(UserAdminBase):
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "usable_password", "password1", "password2"),
            },
        ),
    )
    form = UserChangeForm
    list_display = ("email", "first_name", "last_name", "is_staff")

    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)
        fieldsets = list(self.fieldsets)
        fieldsets[0] = (
            None,
            {"fields": ("email", "password")},
        )
        fieldsets[1] = (
            _("Personal info"),
            {"fields": ("first_name", "last_name", "username")},
        )
        self.fieldsets = tuple(fieldsets)


@register(UserStatus)
class UserStatusAdmin(admin.ModelAdmin):
    list_display = ("user", "verified", "archived", "secondary_email")
    search_fields = ("user__email",)
    list_filter = ("verified", "archived")
    raw_id_fields = ("user",)


@register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "height", "weight", "skin_color", "hair_color", "eye_color")
    search_fields = ("user__email", "job__name")
    list_filter = ("skin_color", "eye_color")
    raw_id_fields = ("user", "job")


@register(Education)
class EducationAdmin(admin.ModelAdmin):
    list_display = ("user", "field", "degree", "start", "end", "status")
    search_fields = ("user__email", "field__name", "degree", "city__name")
    list_filter = ("degree", "status")
    raw_id_fields = ("user", "field")


@register(EducationVerification)
class EducationVerificationAdmin(admin.ModelAdmin):
    list_display = ("education", "method", "is_verified", "created_at", "updated_at")
    search_fields = ("education__user__email", "education__degree", "method")
    list_filter = ("method", "is_verified")
    raw_id_fields = ("education",)


@register(IEEMethod)
class IEEMethodAdmin(admin.ModelAdmin):
    list_display = ("education_verification", "ices_document", "citizen_document", "evaluator")
    search_fields = ("education_verification__education__user__email", "evaluator")
    list_filter = ("evaluator",)
    raw_id_fields = ("education_verification",)


@register(CommunicationMethod)
class CommunicationMethodAdmin(admin.ModelAdmin):
    list_display = ("education_verification", "email", "department", "person", "degree_file")
    search_fields = ("education_verification__education__user__email", "email", "department", "person")
    list_filter = ("department",)
    raw_id_fields = ("education_verification",)
