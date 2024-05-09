from django.contrib.auth.models import UserManager as BaseUserManager
from django.db import models


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
