from common.db_functions import GetKeysByValue
from common.utils import fields_join

from django.contrib.auth.models import UserManager as BaseUserManager
from django.db import models
from django.db.models.functions import JSONObject, Now

from .constants import (
    ORGANIZATION_INVITATION_EXPIRY_DELTA,
    STAGE_ANNOTATIONS,
    ProfileAnnotationNames,
)


class FlexReportProfileManager(models.Manager):
    def get_annotations_dict(self):
        from .models import (
            CanadaVisa,
            CertificateAndLicense,
            Education,
            LanguageCertificate,
            OrganizationMembership,
            Profile,
            User,
            WorkExperience,
        )

        return {
            ProfileAnnotationNames.IS_ORGANIZATION_MEMBER: models.Exists(
                OrganizationMembership.objects.filter(
                    **{
                        fields_join(
                            OrganizationMembership.user,
                            Profile.user.field.related_query_name(),
                            Profile._meta.pk.attname,
                        ): models.OuterRef(Profile._meta.pk.attname)
                    }
                )
            ),
            ProfileAnnotationNames.HAS_PROFILE_INFORMATION: models.Case(
                models.When(
                    models.Q(**{fields_join(Profile.gender, "isnull"): True}),
                    then=models.Value(False),
                ),
                default=models.Value(True),
            ),
            ProfileAnnotationNames.HAS_EDUCATION: models.Exists(
                Education.objects.filter(
                    **{
                        fields_join(
                            Education.user,
                            Profile.user.field.related_query_name(),
                            Profile._meta.pk.attname,
                        ): models.OuterRef(Profile._meta.pk.attname)
                    }
                )
            ),
            ProfileAnnotationNames.HAS_VERIFIED_EDUCATION: models.Exists(
                Education.objects.filter(
                    **{
                        fields_join(
                            Education.user,
                            Profile.user.field.related_query_name(),
                            Profile._meta.pk.attname,
                        ): models.OuterRef(Profile._meta.pk.attname),
                        Education.status.field.name: Education.get_verified_statuses(),
                    }
                )
            ),
            ProfileAnnotationNames.HAS_WORK_EXPERIENCE: models.Exists(
                WorkExperience.objects.filter(
                    **{
                        fields_join(
                            WorkExperience.user,
                            Profile.user.field.related_query_name(),
                            Profile._meta.pk.attname,
                        ): models.OuterRef(Profile._meta.pk.attname)
                    }
                )
            ),
            ProfileAnnotationNames.HAS_VERIFIED_WORK_EXPERIENCE: models.Exists(
                WorkExperience.objects.filter(
                    **{
                        fields_join(
                            WorkExperience.user,
                            Profile.user.field.related_query_name(),
                            Profile._meta.pk.attname,
                        ): models.OuterRef(Profile._meta.pk.attname),
                        WorkExperience.status.field.name: WorkExperience.get_verified_statuses(),
                    }
                )
            ),
            ProfileAnnotationNames.HAS_LANGUAGE_CERTIFICATE: models.Exists(
                LanguageCertificate.objects.filter(
                    **{
                        fields_join(
                            LanguageCertificate.user,
                            Profile.user.field.related_query_name(),
                            Profile._meta.pk.attname,
                        ): models.OuterRef(Profile._meta.pk.attname)
                    }
                )
            ),
            ProfileAnnotationNames.HAS_CERTIFICATE: models.Exists(
                CertificateAndLicense.objects.filter(
                    **{
                        fields_join(
                            CertificateAndLicense.user,
                            Profile.user.field.related_query_name(),
                            Profile._meta.pk.attname,
                        ): models.OuterRef(Profile._meta.pk.attname)
                    }
                )
            ),
            ProfileAnnotationNames.HAS_SKILLS: models.Case(
                models.When(
                    models.Q(**{fields_join(Profile.raw_skills, "len"): models.Value(0)}),
                    then=models.Value(False),
                ),
                default=models.Value(True),
            ),
            ProfileAnnotationNames.HAS_CANADA_VISA: models.Exists(
                CanadaVisa.objects.filter(
                    **{
                        fields_join(
                            CanadaVisa.user,
                            Profile.user.field.related_query_name(),
                            Profile._meta.pk.attname,
                        ): models.OuterRef(Profile._meta.pk.attname)
                    }
                )
            ),
            ProfileAnnotationNames.HAS_INTERESTED_JOBS: models.Exists(
                Profile.interested_jobs.field.related_model.objects.filter(
                    **{
                        fields_join(
                            Profile.interested_jobs.field.related_query_name(),
                            Profile._meta.pk.attname,
                        ): models.OuterRef(Profile._meta.pk.attname)
                    }
                )
            ),
            ProfileAnnotationNames.LAST_LOGIN: models.F(
                fields_join(
                    Profile.user,
                    User.last_login,
                    "delta_days",
                )
            ),
            ProfileAnnotationNames.DATE_JOINED: models.F(
                fields_join(
                    Profile.user,
                    User.date_joined,
                    "delta_days",
                )
            ),
            ProfileAnnotationNames.STAGE_DATA: JSONObject(
                **{annotation_name: models.F(annotation_name) for annotation_name in STAGE_ANNOTATIONS}
            ),
            ProfileAnnotationNames.COMPLETED_STAGES: GetKeysByValue(
                models.F(ProfileAnnotationNames.STAGE_DATA),
                models.Value(True),
            ),
            ProfileAnnotationNames.INCOMPLETE_STAGES: GetKeysByValue(
                models.F(ProfileAnnotationNames.STAGE_DATA),
                models.Value(False),
            ),
            ProfileAnnotationNames.HAS_INCOMPLETE_STAGES: models.Case(
                models.When(
                    models.Q(**{fields_join(ProfileAnnotationNames.INCOMPLETE_STAGES, "len"): 0}),
                    then=models.Value(False),
                ),
                default=models.Value(True),
            ),
        }

    def get_queryset(self):
        return super().get_queryset().annotate(**self.get_annotations_dict())


class CertificateAndLicenseQueryset(models.QuerySet):
    def cpjs(self):
        return self.none()

    def non_cpjs(self):
        return self.all()


CertificateAndLicenseManager = models.Manager.from_queryset(CertificateAndLicenseQueryset)


class UserManager(BaseUserManager):
    def create_user(self, **kwargs):
        kwargs.setdefault("username", kwargs.get(self.model.USERNAME_FIELD))
        return super().create_user(**kwargs)

    def create_superuser(self, **kwargs):
        kwargs.setdefault("username", kwargs.get(self.model.USERNAME_FIELD))
        return super().create_superuser(**kwargs)


class OrganizationInvitationManager(models.Manager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .annotate(
                is_expired=models.Case(
                    models.When(
                        models.Q(created_at__lt=Now() - ORGANIZATION_INVITATION_EXPIRY_DELTA), then=models.Value(True)
                    ),
                    default=False,
                    output_field=models.BooleanField(),
                )
            )
        )
