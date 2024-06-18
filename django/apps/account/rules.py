import rules
from common.predicates import has_perms

from . import permissions
from .models import Organization, User


@rules.predicate
def is_organization_verified(user: User, organization: Organization):
    return organization.status in organization.get_verified_statuses()


rules.add_rule(
    permissions.CanAddOrganizationMembership.name,
    is_organization_verified & has_perms(permissions.CanAddOrganizationMembership.name),
)
