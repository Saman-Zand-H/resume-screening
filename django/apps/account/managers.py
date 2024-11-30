from common.db_functions import ArrayDifference, DateTimeAge, GetKeysByValue
from common.utils import fj

from django.contrib.auth.models import UserManager as BaseUserManager
from django.contrib.postgres.fields.array import ArrayLenTransform
from django.db import models
from django.db.models.functions import JSONObject, Now
from django.db.models.functions.datetime import ExtractDay, ExtractYear, TruncDate
from django.db.models.lookups import In, IsNull, LessThan

from .constants import (
    ORGANIZATION_INVITATION_EXPIRY_DELTA,
    STAGE_ANNOTATIONS,
    STAGE_CHOICES,
    ProfileAnnotationNames,
)


class ProfileManager(models.Manager):
    def get_queryset(self):
        from .models import Profile

        return (
            super()
            .get_queryset()
            .annotate(
                **{
                    Profile.job_type.fget.annotation_name: ArrayDifference(
                        Profile.JobType.values,
                        models.F(Profile.job_type_exclude.field.name),
                    ),
                    Profile.job_location_type.fget.annotation_name: ArrayDifference(
                        Profile.JobLocationType.values,
                        models.F(Profile.job_location_type_exclude.field.name),
                    ),
                }
            )
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
            Resume,
            User,
            WorkExperience,
        )

        return {
            ProfileAnnotationNames.IS_ORGANIZATION_MEMBER: models.Exists(
                OrganizationMembership.objects.filter(
                    **{
                        fj(
                            OrganizationMembership.user,
                            Profile.user.field.related_query_name(),
                            Profile._meta.pk.attname,
                        ): models.OuterRef(Profile._meta.pk.attname)
                    }
                )
            ),
            ProfileAnnotationNames.HAS_PROFILE_INFORMATION: models.Case(
                models.When(
                    models.Q(**{fj(Profile.gender, IsNull.lookup_name): True}),
                    then=models.Value(False),
                ),
                default=models.Value(True),
            ),
            ProfileAnnotationNames.HAS_EDUCATION: models.Exists(
                Education.objects.filter(
                    **{
                        fj(
                            Education.user,
                            Profile.user.field.related_query_name(),
                            Profile._meta.pk.attname,
                        ): models.OuterRef(Profile._meta.pk.attname)
                    }
                )
            ),
            ProfileAnnotationNames.HAS_UNVERIFIED_EDUCATION: models.Exists(
                Education.objects.filter(
                    **{
                        fj(
                            Education.user,
                            Profile.user.field.related_query_name(),
                            Profile._meta.pk.attname,
                        ): models.OuterRef(Profile._meta.pk.attname),
                    }
                ).exclude(
                    **{
                        fj(Education.status, In.lookup_name): Education.get_verified_statuses(),
                    }
                ),
            ),
            ProfileAnnotationNames.HAS_WORK_EXPERIENCE: models.Exists(
                WorkExperience.objects.filter(
                    **{
                        fj(
                            WorkExperience.user,
                            Profile.user.field.related_query_name(),
                            Profile._meta.pk.attname,
                        ): models.OuterRef(Profile._meta.pk.attname)
                    }
                )
            ),
            ProfileAnnotationNames.HAS_UNVERIFIED_WORK_EXPERIENCE: models.Exists(
                WorkExperience.objects.filter(
                    **{
                        fj(
                            WorkExperience.user,
                            Profile.user.field.related_query_name(),
                            Profile._meta.pk.attname,
                        ): models.OuterRef(Profile._meta.pk.attname),
                        WorkExperience.status.field.name: WorkExperience.get_verified_statuses(),
                    }
                ),
                negated=True,
            ),
            ProfileAnnotationNames.HAS_LANGUAGE_CERTIFICATE: models.Exists(
                LanguageCertificate.objects.filter(
                    **{
                        fj(
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
                        fj(
                            CertificateAndLicense.user,
                            Profile.user.field.related_query_name(),
                            Profile._meta.pk.attname,
                        ): models.OuterRef(Profile._meta.pk.attname)
                    }
                )
            ),
            ProfileAnnotationNames.HAS_SKILLS: models.Case(
                models.When(
                    models.Q(**{fj(Profile.raw_skills, ArrayLenTransform.lookup_name): models.Value(0)}),
                    then=models.Value(False),
                ),
                default=models.Value(True),
            ),
            ProfileAnnotationNames.HAS_CANADA_VISA: models.Exists(
                CanadaVisa.objects.filter(
                    **{
                        fj(
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
                        fj(
                            Profile.interested_jobs.field.related_query_name(),
                            Profile._meta.pk.attname,
                        ): models.OuterRef(Profile._meta.pk.attname)
                    }
                )
            ),
            ProfileAnnotationNames.AGE: models.F(
                fj(
                    Profile.birth_date,
                    DateTimeAge.lookup_name,
                    ExtractYear.lookup_name,
                )
            ),
            ProfileAnnotationNames.LAST_LOGIN: models.F(
                fj(
                    Profile.user,
                    User.last_login,
                    TruncDate.lookup_name,
                    DateTimeAge.lookup_name,
                    ExtractDay.lookup_name,
                )
            ),
            ProfileAnnotationNames.DATE_JOINED: models.F(
                fj(
                    Profile.user,
                    User.date_joined,
                    TruncDate.lookup_name,
                    DateTimeAge.lookup_name,
                    ExtractDay.lookup_name,
                )
            ),
            ProfileAnnotationNames.HAS_RESUME: models.Exists(
                Resume.objects.filter(
                    **{
                        fj(
                            Resume.user,
                            Profile.user.field.related_query_name(),
                            Profile._meta.pk.attname,
                        ): models.OuterRef(Profile._meta.pk.attname)
                    }
                )
            ),
            ProfileAnnotationNames.STAGE_DATA: JSONObject(
                **{annotation_name: models.F(annotation_name) for annotation_name in STAGE_ANNOTATIONS}
            ),
            ProfileAnnotationNames.COMPLETED_STAGES: GetKeysByValue(
                models.F(ProfileAnnotationNames.STAGE_DATA),
                models.Value(True),
                choices=STAGE_CHOICES,
            ),
            ProfileAnnotationNames.INCOMPLETE_STAGES: GetKeysByValue(
                models.F(ProfileAnnotationNames.STAGE_DATA),
                models.Value(False),
                choices=STAGE_CHOICES,
            ),
            ProfileAnnotationNames.HAS_INCOMPLETE_STAGES: models.Case(
                models.When(
                    models.Q(**{fj(ProfileAnnotationNames.INCOMPLETE_STAGES, ArrayLenTransform.lookup_name): 0}),
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
        from .models import User

        kwargs.setdefault(fj(User.username), kwargs.get(self.model.USERNAME_FIELD))
        return super().create_user(**kwargs)

    def create_superuser(self, **kwargs):
        from .models import User

        kwargs.setdefault(fj(User.username), kwargs.get(self.model.USERNAME_FIELD))
        return super().create_superuser(**kwargs)


class OrganizationInvitationManager(models.Manager):
    def get_queryset(self):
        from .models import OrganizationInvitation

        return (
            super()
            .get_queryset()
            .annotate(
                is_expired=models.Case(
                    models.When(
                        models.Q(
                            **{
                                fj(
                                    OrganizationInvitation.created_at,
                                    LessThan.lookup_name,
                                ): Now() - ORGANIZATION_INVITATION_EXPIRY_DELTA
                            }
                        ),
                        then=models.Value(True),
                    ),
                    default=False,
                    output_field=models.BooleanField(),
                )
            )
        )
