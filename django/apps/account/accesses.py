from itertools import chain
from operator import methodcaller
from typing import Callable, List, Optional, Type

from common.utils import get_all_subclasses, fields_join
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
    title: Optional[str] = None
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


@predicates.predicate
def has_organization_membership(kwargs: dict):
    parsed_kwargs = AccessPredicateArgument.model_validate(kwargs)
    user = parsed_kwargs.user

    return OrganizationMembership.objects.filter(
        **{
            OrganizationMembership.user.field.name: user,
            fields_join(
                OrganizationMembership.organization.field.related_query_name(), Organization.status
            ): Organization.get_verified_statuses(),
        }
    ).exists()


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
            add_rule(access.slug, access.predicate | is_superuser)

    @classmethod
    def register_all_rules(cls) -> None:
        for access in get_all_subclasses(cls):
            access.register_rules()


class OrganizationProfileContainer(AccessContainer):
    COMPANY_EDITOR = AccessType(
        slug="company-editor",
        title="Can edit company information",
        predicate=is_organization_member,
    )
    CONTACT_EDITOR = AccessType(
        slug="contact-editor",
        title="Can edit company contact information",
        predicate=is_organization_member,
    )
    VERIFIER = AccessType(
        slug="verifier",
        title="Has access to company verification process",
        predicate=is_organization_member,
    )
    ADMIN = AccessType(
        slug="admin",
        title="Can manage company profile",
        predicate=is_organization_member,
    )


class OrganizationMembershipContainer(AccessContainer):
    CREATOR = AccessType(
        slug="create-organization-membership",
        title="Can create organization memberships",
        predicate=is_organization_member,
    )
    INVITOR = AccessType(
        slug="invite-organization-membership",
        title="Can invite users to organization",
        predicate=is_organization_member,
    )
    EDITOR = AccessType(
        slug="edit-organization-membership",
        title="Can edit organization memberships",
        predicate=is_organization_member,
    )
    VIEWER = AccessType(
        slug="view-organization-membership",
        title="Can view organization memberships",
        predicate=is_organization_member,
    )
    ADMIN = AccessType(
        slug="admin-organization-membership",
        title="Can manage organization memberships",
        predicate=is_organization_member,
    )


class JobPositionContainer(AccessContainer):
    CREATEOR = AccessType(
        slug="create-job-position",
        title="Can create job positions",
        predicate=(is_organization_member & is_organization_verified),
    )
    EDITOR = AccessType(
        slug="edit-job-position",
        title="Can edit job positions",
        predicate=(is_organization_member & is_organization_verified),
    )
    VIEWER = AccessType(
        slug="view-job-position",
        title="Can view job positions",
        predicate=is_organization_member,
    )
    STATUS_CHANGER = AccessType(
        slug="change-job-position-status",
        title="Can change job position status",
        predicate=(is_organization_member & is_organization_verified),
    )
    HIRING_STATUS_CHANGER = AccessType(
        slug="change-job-position-hiring-status",
        title="Can change job position hiring status",
        predicate=(is_organization_member & is_organization_verified),
    )
    ADMIN = AccessType(
        slug="admin-job-position",
        title="Can manage job positions",
        predicate=(is_organization_member & is_organization_verified),
    )

    SKILL_CREATOR = AccessType(
        slug="skill-creator",
        title="Can create job position skills",
        predicate=has_organization_membership,
    )
