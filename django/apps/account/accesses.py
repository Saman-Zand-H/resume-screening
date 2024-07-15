from itertools import chain
from operator import methodcaller
from typing import Callable, List, Optional, Type

from common.utils import get_all_subclasses
from pydantic import BaseModel, InstanceOf
from rules import predicates
from rules.rulesets import add_rule

from django.db.models import Model, QuerySet

from .models import Organization, OrganizationMembership, User


class AccessPredicateArgument(BaseModel):
    user: Optional[InstanceOf[Model]] = None
    instance: Optional[InstanceOf[Model]] = None


class AccessType(BaseModel):
    slug: str
    description: Optional[str] = None
    predicate: Optional[Callable[[AccessPredicateArgument], bool]] = predicates.always_allow


@predicates.predicate
def is_superuser(kwargs: dict):
    parsed_kwargs = AccessPredicateArgument.model_validate(kwargs)
    user = parsed_kwargs.user

    assert isinstance(user, User), f"Invalid argument type: {user}; expected: {User}"
    return user.is_superuser


@predicates.predicate
def is_organization_verified(kwargs: dict):
    parsed_kwargs = AccessPredicateArgument.model_validate(kwargs)
    user = parsed_kwargs.user
    instance = parsed_kwargs.instance

    if not instance:
        return False

    assert isinstance(user, User) and isinstance(
        instance, Organization
    ), f"Invalid argument types: {user}, {instance}; expected: {User}, {Organization}"

    return instance.status in Organization.get_verified_statuses()


@predicates.predicate
def is_organization_member(kwargs: dict):
    parsed_kwargs = AccessPredicateArgument.model_validate(kwargs)
    user = parsed_kwargs.user
    instance = parsed_kwargs.instance

    if not instance:
        return False

    assert isinstance(user, User) and isinstance(
        instance, Organization
    ), f"Invalid argument types {user}, {instance}; expected: {User}, {Organization}"

    memberships: QuerySet[OrganizationMembership] = getattr(
        user, OrganizationMembership.user.field.related_query_name()
    )
    return memberships.filter(**{OrganizationMembership.organization.field.name: instance}).exists()


class AccessContainer:
    @classmethod
    def get_accesses(cls) -> List[Type[AccessType]]:
        return [value for cls in cls.__mro__ for value in cls.__dict__.values() if isinstance(value, AccessType)]

    @classmethod
    def get_all_accesses(cls) -> List[AccessType]:
        return list(chain.from_iterable(map(methodcaller("get_accesses"), get_all_subclasses(cls))))

    @classmethod
    def register_rules(cls) -> None:
        for access in cls.get_accesses():
            add_rule(access.slug, access.predicate)

    @classmethod
    def register_all_rules(cls) -> None:
        for access in get_all_subclasses(cls):
            access.register_rules()


class OrganizationProfileContainer(AccessContainer):
    COMPANY_EDITOR = AccessType(
        slug="company-editor",
        description="Can edit company information",
        predicate=is_organization_member | is_superuser,
    )
    CONTACT_EDITOR = AccessType(
        slug="contact-editor",
        description="Can edit company contact information",
        predicate=is_organization_member | is_superuser,
    )
    VERIFIER = AccessType(
        slug="verifier",
        description="Has access to company verification process",
        predicate=is_organization_member | is_superuser,
    )
    ADMIN = AccessType(
        slug="admin",
        description="Can manage company profile",
        predicate=is_organization_member | is_superuser,
    )


class OrganizationMembershipContainer(AccessContainer):
    CREATOR = AccessType(
        slug="create-organization-membership",
        description="Can create organization memberships",
        predicate=is_organization_member | is_superuser,
    )
    INVITOR = AccessType(
        slug="invite-organization-membership",
        description="Can invite users to organization",
        predicate=is_organization_member | is_superuser,
    )
    EDITOR = AccessType(
        slug="edit-organization-membership",
        description="Can edit organization memberships",
        predicate=is_organization_member | is_superuser,
    )
    VIEWER = AccessType(
        slug="view-organization-membership",
        description="Can view organization memberships",
        predicate=is_organization_member | is_superuser,
    )
    ADMIN = AccessType(
        slug="admin-organization-membership",
        description="Can manage organization memberships",
        predicate=is_organization_member | is_superuser,
    )


class JobPositionContainer(AccessContainer):
    CREATEOR = AccessType(
        slug="create-job-position",
        description="Can create job positions",
        predicate=(is_organization_member & is_organization_verified) | is_superuser,
    )
    EDITOR = AccessType(
        slug="edit-job-position",
        description="Can edit job positions",
        predicate=(is_organization_member & is_organization_verified) | is_superuser,
    )
    VIEWER = AccessType(
        slug="view-job-position",
        description="Can view job positions",
        predicate=is_organization_member | is_superuser,
    )
    STATUS_CHANGER = AccessType(
        slug="change-job-position-status",
        description="Can change job position status",
        predicate=(is_organization_member & is_organization_verified) | is_superuser,
    )
    HIRING_STATUS_CHANGER = AccessType(
        slug="change-job-position-hiring-status",
        description="Can change job position hiring status",
        predicate=(is_organization_member & is_organization_verified) | is_superuser,
    )
    ADMIN = AccessType(
        slug="admin-job-position",
        description="Can manage job positions",
        predicate=(is_organization_member & is_organization_verified) | is_superuser,
    )
