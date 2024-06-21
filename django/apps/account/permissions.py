from common.permissions import Rule


class CanAddOrganizationMembership(Rule):
    name = "add_organization_membership"
    description = "Can add organization membership"
