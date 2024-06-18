import rules

from . import permissions
from .models import Organization, User


@rules.predicate
def is_organization_verified(user: User, organization: Organization):
    return organization.status in organization.get_verified_statuses()


rules.add_perm(
    permissions.CanAddOrganizationMembership.name,
    is_organization_verified & rules.has_perm(permissions.CanAddOrganizationMembership.name),
)
