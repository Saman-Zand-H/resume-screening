from common.utils import fields_join, nested_getattr
from import_export import fields
from import_export.resources import ModelResource

from django.conf import settings
from django.utils.translation import gettext_lazy as _

from ..models import (
    CertificateAndLicense,
    Contact,
    Education,
    LanguageCertificate,
    Profile,
    User,
    WorkExperience,
)


class ProfileResource(ModelResource):
    phone_number = fields.Field(column_name=_("Phone Number"))

    def dehydrate_birth_date(self, obj: Profile):
        return (obj.birth_date and obj.birth_date.strftime("%Y-%m-%d")) or "_"

    def dehydrate_phone_number(self, obj: Profile):
        return ", ".join(
            display_value
            for instance in Contact.objects.filter(**{Contact.type.field.name: Contact.Type.PHONE}).filter(
                contactable__profile=obj
            )
            if (display_dict := instance.get_display_name_and_link()) and (display_value := display_dict.get("display"))
        )

    def dehydrate_avatar(self, obj: Profile):
        return obj.avatar and f"{settings.SITE_DOMAIN.rstrip("/")}/{obj.avatar.file}"

    def dehydrate_gender(self, obj: Profile):
        return obj.get_gender_display()

    def dehydrate_full_name(self, obj: Profile):
        return obj.user.full_name

    class Meta:
        model = Profile
        fields = [
            "email",
            "full_name",
            "phone_number",
            Profile.birth_date.field.name,
            Profile.avatar.field.name,
            Profile.gender.field.name,
        ]


class EducationResource(ModelResource):
    email = fields.Field(column_name=_("Email"))
    phone_number = fields.Field(column_name=_("Phone Number"))
    duration = fields.Field(column_name=_("Duration"))

    def dehydrate_duration(self, obj):
        return obj.duration

    def dehydrate_status(self, obj: Education):
        return obj.get_status_display()

    def dehydrate_city(self, obj: Education):
        return obj.city.display_name

    def dehydrate_field(self, obj: Education):
        return obj.field.name

    def dehydrate_degree(self, obj: Education):
        return obj.get_degree_display()

    def dehydrate_university(self, obj: Education):
        return obj.university.name

    def dehydrate_email(self, obj: Education):
        return nested_getattr(obj, fields_join(Education.profile, User.email))

    def dehydrate_phone_number(self, obj: Education):
        return ", ".join(
            display_value
            for instance in Contact.objects.filter(**{Contact.type.field.name: Contact.Type.PHONE}).filter(
                contactable__profile__user=obj.user
            )
            if (display_dict := instance.get_display_name_and_link()) and (display_value := display_dict.get("display"))
        )

    class Meta:
        model = Education
        fields = [
            "email",
            "phone_number",
            Education.status.field.name,
            Education.city.field.name,
            Education.field.field.name,
            Education.degree.field.name,
            Education.university.field.name,
            "duration",
        ]


class WorkExperienceResource(ModelResource):
    email = fields.Field(column_name=_("Email"))
    phone_number = fields.Field(column_name=_("Phone Number"))
    duration = fields.Field(column_name=_("Duration"))

    def dehydrate_duration(self, obj):
        return obj.duration

    def dehydrate_industry(self, obj: WorkExperience):
        return obj.industry.title

    def dehydrate_grade(self, obj: WorkExperience):
        return obj.get_grade_display()

    def dehydrate_company(self, obj: WorkExperience):
        return obj.organization

    def dehydrate_city(self, obj: WorkExperience):
        return obj.city.display_name

    def dehydrate_email(self, obj: WorkExperience):
        return nested_getattr(obj, fields_join(WorkExperience.profile, User.email))

    def dehydrate_phone_number(self, obj: WorkExperience):
        return ", ".join(
            display_value
            for instance in Contact.objects.filter(**{Contact.type.field.name: Contact.Type.PHONE}).filter(
                contactable__profile__user=obj.user
            )
            if (display_dict := instance.get_display_name_and_link()) and (display_value := display_dict.get("display"))
        )

    def dehydrate_status(self, obj: WorkExperience):
        return obj.get_status_display()

    class Meta:
        model = WorkExperience
        fields = [
            "email",
            "phone_number",
            WorkExperience.job_title.field.name,
            WorkExperience.status.field.name,
            WorkExperience.grade.field.name,
            WorkExperience.organization.field.name,
            WorkExperience.city.field.name,
            WorkExperience.industry.field.name,
            WorkExperience.skills.field.name,
            "duration",
        ]


class LanguageCertificateResource(ModelResource):
    email = fields.Field(column_name=_("Email"))
    phone_number = fields.Field(column_name=_("Phone Number"))
    duration = fields.Field(column_name=_("Duration"))

    def dehydrate_duration(self, obj):
        return obj.duration

    def dehydrate_level(self, obj: LanguageCertificate):
        return obj.get_level_display()

    def dehydrate_scores(self, obj: LanguageCertificate):
        return obj.scores

    def dehydrate_email(self, obj: LanguageCertificate):
        return nested_getattr(obj, fields_join(LanguageCertificate.profile, User.email))

    def dehydrate_phone_number(self, obj: LanguageCertificate):
        return ", ".join(
            display_value
            for instance in Contact.objects.filter(**{Contact.type.field.name: Contact.Type.PHONE}).filter(
                contactable__profile__user=obj.user
            )
            if (display_dict := instance.get_display_name_and_link()) and (display_value := display_dict.get("display"))
        )

    def dehydrate_test(self, obj: LanguageCertificate):
        return obj.test.title

    def dehydrate_status(self, obj: LanguageCertificate):
        return obj.get_status_display()

    class Meta:
        model = LanguageCertificate
        fields = [
            "email",
            "phone_number",
            LanguageCertificate.status.field.name,
            LanguageCertificate.language.field.name,
            LanguageCertificate.test.field.name,
            "duration",
            "scores",
        ]


class CertificateAndLicenseResource(ModelResource):
    email = fields.Field(column_name=_("Email"))
    phone_number = fields.Field(column_name=_("Phone Number"))
    duration = fields.Field(column_name=_("Duration"))

    def dehydrate_duration(self, obj):
        return obj.duration

    def dehydrate_email(self, obj: CertificateAndLicense):
        return nested_getattr(obj, fields_join(CertificateAndLicense.profile, User.email))

    def dehydrate_phone_number(self, obj: CertificateAndLicense):
        return ", ".join(
            display_value
            for instance in Contact.objects.filter(**{Contact.type.field.name: Contact.Type.PHONE}).filter(
                contactable__profile__user=obj.user,
            )
            if (display_dict := instance.get_display_name_and_link()) and (display_value := display_dict.get("display"))
        )

    def dehydrate_issuing_organization(self, obj: CertificateAndLicense):
        return obj.issuing_organization

    def dehydrate_issue_date(self, obj: CertificateAndLicense):
        return obj.issue_date and obj.issue_date.strftime("%Y-%m-%d")

    def dehydrate_expiration_date(self, obj: CertificateAndLicense):
        return obj.expiration_date and obj.expiration_date.strftime("%Y-%m-%d")

    def dehydrate_status(self, obj: CertificateAndLicense):
        return obj.get_status_display()

    class Meta:
        model = CertificateAndLicense
        fields = [
            "email",
            "phone_number",
            CertificateAndLicense.status.field.name,
            CertificateAndLicense.title.field.name,
            CertificateAndLicense.certifier.field.name,
            "duration",
        ]
