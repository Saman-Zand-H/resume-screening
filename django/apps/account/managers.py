from django.contrib.auth.models import UserManager as BaseUserManager
from django.db import models
from django.db.models.functions import Now

from .constants import ORGANIZATION_INVITATION_EXPIRY_DELTA, AnnotationNames


class ProfileManager(models.Manager):
    def get_queryset(self):
        from .models import OrganizationMembership

        return (
            super()
            .get_queryset()
            .annotate(
                **{
                    AnnotationNames.IS_ORGANIZATION_MEMBER: models.Exists(
                        OrganizationMembership.objects.filter(
                            **{OrganizationMembership.user.field.name: models.OuterRef("user")}
                        )
                    )
                }
            )
        )


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
