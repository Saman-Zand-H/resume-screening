from common.utils import LOOKUP_SEP, fields_join, nested_getattr
from import_export import fields
from import_export.resources import ModelResource

from django.conf import settings
from django.urls import reverse_lazy
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
    email = fields.Field(column_name=_("Email"))
    full_name = fields.Field(column_name=_("Full Name"))
    phone_number = fields.Field(column_name=_("Phone Number"))
    educations = fields.Field(column_name=_("Educations"))
    work_experiences = fields.Field(column_name=_("Work Experiences"))
    language_certificates = fields.Field(column_name=_("Language Certificates"))
    certificate_and_licenses = fields.Field(column_name=_("Certificates and Licenses"))
    birth_date = fields.Field(column_name=_("Birth Date"), default="_")
    last_login = fields.Field(column_name=_("Last Login"), default="_")
    date_joined = fields.Field(column_name=_("Date Joined"), default="_")
    has_education = fields.Field(column_name=_("Has Education"))
    has_work_experience = fields.Field(column_name=_("Has Work Experience"))
    has_language_certificate = fields.Field(column_name=_("Has Language Certificate"))
    has_certificate_and_license = fields.Field(column_name=_("Has Certificate and License"))

    def dehydrate_educations(self, obj: Profile):
        return "\n\n".join(
            "\n".join(
                [
                    f"Degree: {education.get_degree_display()}",
                    f"Status: {education.get_status_display()}",
                    f"University: {education.university.name}",
                    f"Admin Link: {settings.SITE_DOMAIN}{reverse_lazy('admin:auth_account_education_change', args=[education.pk])}",
                ]
            )
            for education in Education.objects.filter(**{Education.user.field.name: obj.user})
        )

    def dehydrate_work_experiences(self, obj: Profile):
        return "\n\n".join(
            "\n".join(
                [
                    f"Job Title: {work_experience.job_title}",
                    f"Status: {work_experience.get_status_display()}",
                    f"Organization: {work_experience.organization}",
                    f"Admin Link: {settings.SITE_DOMAIN}{reverse_lazy('admin:auth_account_workexperience_change', args=[work_experience.pk])}",
                ]
            )
            for work_experience in WorkExperience.objects.filter(**{WorkExperience.user.field.name: obj.user})
        )

    def dehydrate_certificate_and_licenses(self, obj: Profile):
        return "\n\n".join(
            "\n".join(
                [
                    f"Title: {certificate_and_license.title}",
                    f"Status: {certificate_and_license.get_status_display()}",
                    f"Certifier: {certificate_and_license.certifier}",
                    f"Admin Link: {settings.SITE_DOMAIN}{reverse_lazy('admin:auth_account_certificateandlicense_change', args=[certificate_and_license.pk])}",
                ]
            )
            for certificate_and_license in CertificateAndLicense.objects.filter(
                **{CertificateAndLicense.user.field.name: obj.user}
            )
        )

    def dehydrate_language_certificates(self, obj: Profile):
        return "\n\n".join(
            "\n".join(
                [
                    f"Language: {language_certificate.language}",
                    f"Test: {language_certificate.test.title}",
                    f"Scores: {language_certificate.scores}",
                    f"Admin Link: {settings.SITE_DOMAIN}{reverse_lazy('admin:auth_account_languagecertificate_change', args=[language_certificate.pk])}",
                ]
            )
            for language_certificate in LanguageCertificate.objects.filter(
                **{LanguageCertificate.user.field.name: obj.user}
            )
        )

    def dehydrate_phone_number(self, obj: Profile):
        return ", ".join(
            display_value
            for instance in Contact.objects.filter(**{Contact.type.field.name: Contact.Type.PHONE}).filter(
                contactable__profile=obj
            )
            if (display_dict := instance.get_display_name_and_link()) and (display_value := display_dict.get("display"))
        )

    def dehydrate_avatar(self, obj: Profile):
        return obj.avatar and f"{settings.SITE_DOMAIN}{obj.avatar.file}"

    def dehydrate_gender(self, obj: Profile):
        return obj.get_gender_display()

    def dehydrate_full_name(self, obj: Profile):
        return obj.user.full_name

    def dehydrate_email(self, obj: Profile):
        return obj.user.email

    def dehydrate_last_login(self, obj: Profile):
        return obj.user.last_login.replace(tzinfo=None) if obj.user.last_login else None

    def dehydrate_date_joined(self, obj: Profile):
        return obj.user.date_joined.replace(tzinfo=None) if obj.user.date_joined else None

    def dehydrate_has_education(self, obj: Profile):
        return "✓" if obj.user.educations.exists() else "×"

    def dehydrate_has_work_experience(self, obj: Profile):
        return "✓" if obj.user.workexperiences.exists() else "×"

    def dehydrate_has_language_certificate(self, obj: Profile):
        return "✓" if obj.user.languagecertificates.exists() else "×"

    def dehydrate_has_certificate_and_license(self, obj: Profile):
        return "✓" if obj.user.certificateandlicenses.exists() else "×"

    class Meta:
        model = Profile
        fields = [
            "email",
            "full_name",
            "phone_number",
            "educations",
            Profile.birth_date.field.name,
            Profile.avatar.field.name,
            Profile.gender.field.name,
            Profile.credits.field.name,
            Profile.score.field.name,
            "work_experiences",
            "language_certificates",
            "certificate_and_licenses",
            "last_login",
            "date_joined",
            "has_education",
            "has_work_experience",
            "has_language_certificate",
            "has_certificate_and_license",
        ]
        widgets = {
            Profile.birth_date.field.name: {"format": "%Y-%m-%d"},
        }


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
        return nested_getattr(obj, fields_join(Education.user, User.email), LOOKUP_SEP)

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
        return nested_getattr(obj, fields_join(WorkExperience.user, User.email), delimeter=LOOKUP_SEP)

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

    def dehydrate_scores(self, obj: LanguageCertificate):
        return obj.scores

    def dehydrate_email(self, obj: LanguageCertificate):
        return nested_getattr(obj, fields_join(LanguageCertificate.user, User.email), delimeter=LOOKUP_SEP)

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
        return nested_getattr(obj, fields_join(CertificateAndLicense.user, User.email), delimeter=LOOKUP_SEP)

    def dehydrate_phone_number(self, obj: CertificateAndLicense):
        return ", ".join(
            display_value
            for instance in Contact.objects.filter(**{Contact.type.field.name: Contact.Type.PHONE}).filter(
                contactable__profile__user=obj.user,
            )
            if (display_dict := instance.get_display_name_and_link()) and (display_value := display_dict.get("display"))
        )

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
