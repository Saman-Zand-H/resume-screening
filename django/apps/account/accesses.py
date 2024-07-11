from itertools import chain
from operator import methodcaller
from typing import Callable, List, Optional, Type, TypedDict

from common.utils import get_all_subclasses
from pydantic import BaseModel
from rules import predicates
from rules.rulesets import add_rule

from django.db.models import Model


class AccessPredicateArgument(TypedDict):
    user: Model
    access_slug: str
    instance: Optional[Model]


class AccessType(BaseModel):
    slug: str
    description: Optional[str] = None
    predicate: Optional[Callable[[AccessPredicateArgument], bool]] = predicates.always_allow


@predicates.predicate
def is_organization_verified(user, instance):
    from .models import Organization, User

    assert isinstance(user, User) and isinstance(instance, Organization), "Invalid argument types"

    return instance.status in Organization.get_verified_statuses()


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
    company_editor = AccessType(
        slug="company-editor",
        description="Can edit company information",
        predicate=predicates.always_allow,
    )
    contact_editor = AccessType(
        slug="contact-editor",
        description="Can edit company contact information",
        predicate=predicates.always_allow,
    )
    verifier = AccessType(
        slug="verifier",
        description="Has access to company verification process",
        predicate=predicates.always_allow,
    )


class JobPositionContainer(AccessContainer):
    create = AccessType(
        slug="create-job-position",
        description="Can create job positions",
        predicate=is_organization_verified,
    )
    edit = AccessType(
        slug="edit-job-position",
        description="Can edit job positions",
        predicate=is_organization_verified,
    )
    view = AccessType(
        slug="view-job-position",
        description="Can view job positions",
        predicate=predicates.always_allow,
    )
    change_status = AccessType(
        slug="change-job-position-status",
        description="Can change job position status",
        predicate=is_organization_verified,
    )
    change_hiring_status = AccessType(
        slug="change-job-position-hiring-status",
        description="Can change job position hiring status",
        predicate=is_organization_verified,
    )
    change_hiring_status = AccessType(
        slug="change-job-position-hiring-status",
        description="Can change job position hiring status",
        predicate=is_organization_verified,
    )
