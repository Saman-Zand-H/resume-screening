from common.permissions import PermissionClass


class CanAddOrganizationMembership(PermissionClass):
    name = "add_organization_membership"
    description = "Can add organization membership"
