from typing import Annotated, Callable, List, Optional, Type

from common.utils import get_all_subclasses
from pydantic import AfterValidator, BaseModel
from rules import predicates
from rules.rulesets import add_rule

from django.core.validators import validate_slug as django_validate_slug
from django.utils.functional import classproperty, lazy


class AccessType(BaseModel):
    slug: Annotated[str, AfterValidator(django_validate_slug)]
    description: Optional[str] = None
    predicate: Optional[Callable] = predicates.always_allow
    default_predicate: Optional[Callable] = predicates.always_deny


@predicates.predicate
def check_user_ownership(user, instance):
    from .models import User

    assert isinstance(user, User) and hasattr(instance, "user")
    return instance.user == user


class AccessContainer:
    @classmethod
    def get_accesses(cls) -> List[Type[AccessType]]:
        return list(filter(lambda access: isinstance(access, AccessType), cls.__dict__.values()))

    @lazy
    @classmethod
    def register_rules(cls) -> None:
        for access in cls.get_accesses():
            add_rule(access.slug, access.predicate)

    @classmethod
    def register_all_rules(cls) -> None:
        for access in get_all_subclasses(cls):
            access.register_rules()


class CRUDAccessContainer(AccessContainer):
    @staticmethod
    def get_access_name() -> str:
        return None

    @classproperty
    def CREATOR(cls):
        return AccessType(
            slug=f"can_add_{(access_name:=cls.get_access_name())}",
            description=f"Can add all {access_name}",
            predicate=check_user_ownership,
            default_predicate=check_user_ownership,
        )

    @classproperty
    def EDITOR(cls):
        return AccessType(
            slug=f"can_edit_{(access_name:=cls.get_access_name())}",
            description=f"Can edit all {access_name}",
            predicate=predicates.always_deny,
        )

    @classproperty
    def VIEWER(cls):
        return AccessType(
            slug=f"can_view_{(access_name:=cls.get_access_name())}",
            description=f"Can view all {access_name}",
            predicate=check_user_ownership,
            default_predicate=check_user_ownership,
        )

    @classproperty
    def DELETER(cls):
        return AccessType(
            slug=f"can_delete_{(access_name:=cls.get_access_name())}",
            description=f"Can delete all {access_name}",
            predicate=predicates.always_deny,
        )

    @classproperty
    def ADMIN(cls):
        return AccessType(
            slug=f"can_admin_{(access_name:=cls.get_access_name())}",
            description=f"Can manage all {access_name}",
            predicate=predicates.always_deny,
        )


class VerificationAccessContainer(AccessContainer):
    @staticmethod
    def get_access_name() -> str:
        return None

    @classproperty
    def VERIFIER(cls):
        return AccessType(
            slug=f"can_verify_{(access_name:=cls.get_access_name())}",
            description=f"Can verify all {access_name} instances",
            predicate=predicates.always_deny,
        )

    @classproperty
    def EDITOR(cls):
        return AccessType(
            slug=f"can_edit_{(access_name:=cls.get_access_name())}_verification",
            description=f"Can edit all {access_name} verifications",
            predicate=predicates.always_deny,
        )

    @classproperty
    def METHOD_CHANGER(cls):
        return AccessType(
            slug=f"can_change_verification_method_{(access_name:=cls.get_access_name())}",
            description=f"Can change verification methods for all {access_name}",
            predicate=check_user_ownership,
            default_predicate=check_user_ownership,
        )

    @classproperty
    def DELETER(cls):
        return AccessType(
            slug=f"can_delete_{(access_name:=cls.get_access_name())}_verification",
            description=f"Can delete all {access_name} verifications",
            predicate=predicates.always_deny,
        )

    @classproperty
    def ADMIN(cls):
        return AccessType(
            slug=f"can_admin_{(access_name:=cls.get_access_name())}_verification",
            description=f"Can manage all {access_name} verifications",
            predicate=predicates.always_deny,
        )


class EducationAccess(CRUDAccessContainer):
    @staticmethod
    def get_access_name() -> str:
        return "education"


class EducationVerificationAccess(VerificationAccessContainer):
    @staticmethod
    def get_access_name() -> str:
        return "education"


class WorkExperienceAccess(CRUDAccessContainer):
    @staticmethod
    def get_access_name() -> str:
        return "work_experience"


class WorkExperienceVerificationAccess(VerificationAccessContainer):
    @staticmethod
    def get_access_name() -> str:
        return "work_experience"


class LanguageCertificateAccess(CRUDAccessContainer):
    @staticmethod
    def get_access_name() -> str:
        return "language_certificate"


class LanguageCertificateVerificationAccess(VerificationAccessContainer):
    @staticmethod
    def get_access_name() -> str:
        return "language_certificate"


class CertificateAndLicenseAccess(CRUDAccessContainer):
    @staticmethod
    def get_access_name() -> str:
        return "certificate_and_license"


class CertificateAndLicenseVerificationAccess(VerificationAccessContainer):
    @staticmethod
    def get_access_name() -> str:
        return "certificate_and_license"


class CanadaVisaAccess(CRUDAccessContainer):
    @staticmethod
    def get_access_name() -> str:
        return "canada_visa"


class ContactAccess(CRUDAccessContainer):
    @staticmethod
    def get_access_name() -> str:
        return "contact"


class OrganizationAccess(CRUDAccessContainer):
    @staticmethod
    def get_access_name() -> str:
        return "organization"


class OrganizationVerificationAccess(VerificationAccessContainer):
    @staticmethod
    def get_access_name() -> str:
        return "organization"


class OrganizationMembershipAccess(CRUDAccessContainer):
    @staticmethod
    def get_access_name() -> str:
        return "organization_membership"


class OrganizationMembershipRoleAccess(CRUDAccessContainer):
    @staticmethod
    def get_access_name() -> str:
        return "organization_membership_role"


class OrganizationInvitationAccess(CRUDAccessContainer):
    @staticmethod
    def get_access_name() -> str:
        return "organization_invitation"
