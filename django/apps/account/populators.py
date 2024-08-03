from typing import List, NamedTuple

from common.populators import BasePopulator

from .accesses import AccessContainer, AccessType
from .choices import DefaultRoles
from .models import Access, Role, SupportTicketCategory


class RoleAccess(NamedTuple):
    role: Role
    accesses: List[AccessType]


class AccessPopulator(BasePopulator):
    def populate(self):
        access_roles = [
            RoleAccess(
                role=Role(
                    slug=DefaultRoles.OWNER,
                    title=DefaultRoles.OWNER.label,
                    description="Has access to everything",
                ),
                accesses=[
                    Access(**{Access.slug.field.name: access.slug, Access.title.field.name: access.title})
                    for access in AccessContainer.get_all_accesses()
                ],
            )
        ]

        Access.objects.bulk_create(
            [
                Access(
                    **{
                        Access.slug.field.name: access.slug,
                        Access.title.field.name: access.title,
                    }
                )
                for role in access_roles
                for access in role.accesses
            ],
            update_conflicts=True,
            update_fields=[Access.title.field.name],
            unique_fields=[Access.slug.field.name],
            batch_size=20,
        )

        Role.objects.bulk_create(
            [access_role.role for access_role in access_roles],
            update_conflicts=True,
            update_fields=[Role.description.field.name],
            unique_fields=[Role.slug.field.name],
            batch_size=20,
        )

        (RoleAccessThrough := Role.accesses.through).objects.bulk_create(
            [
                RoleAccessThrough(
                    role_id=access_role.role.slug,
                    access_id=access.slug,
                )
                for access_role in access_roles
                for access in access_role.accesses
            ],
            batch_size=20,
            ignore_conflicts=True,
        )


class SupportTicketCategoryPopulator(BasePopulator):
    def populate(self):
        instance_dicts = [
            {
                SupportTicketCategory.title.field.name: "Profile",
                SupportTicketCategory.types.field.name: [
                    SupportTicketCategory.Type.JOB_SEEKER,
                    SupportTicketCategory.Type.ORGANIZATION,
                ],
            },
            {
                SupportTicketCategory.title.field.name: "Resume",
                SupportTicketCategory.types.field.name: [SupportTicketCategory.Type.JOB_SEEKER],
            },
            {
                SupportTicketCategory.title.field.name: "Verification",
                SupportTicketCategory.types.field.name: [
                    SupportTicketCategory.Type.JOB_SEEKER,
                    SupportTicketCategory.Type.ORGANIZATION,
                ],
            },
            {
                SupportTicketCategory.title.field.name: "Visa",
                SupportTicketCategory.types.field.name: [SupportTicketCategory.Type.JOB_SEEKER],
            },
            {
                SupportTicketCategory.title.field.name: "Academy",
                SupportTicketCategory.types.field.name: [SupportTicketCategory.Type.JOB_SEEKER],
            },
            {
                SupportTicketCategory.title.field.name: "Assessment",
                SupportTicketCategory.types.field.name: [SupportTicketCategory.Type.JOB_SEEKER],
            },
            {
                SupportTicketCategory.title.field.name: "Job Suggestion",
                SupportTicketCategory.types.field.name: [SupportTicketCategory.Type.JOB_SEEKER],
            },
            {
                SupportTicketCategory.title.field.name: "Job Position",
                SupportTicketCategory.types.field.name: [SupportTicketCategory.Type.ORGANIZATION],
            },
            {
                SupportTicketCategory.title.field.name: "Hiring",
                SupportTicketCategory.types.field.name: [SupportTicketCategory.Type.ORGANIZATION],
            },
            {
                SupportTicketCategory.title.field.name: "Invitation & Memberships",
                SupportTicketCategory.types.field.name: [SupportTicketCategory.Type.ORGANIZATION],
            },
            {
                SupportTicketCategory.title.field.name: "Finances",
                SupportTicketCategory.types.field.name: [SupportTicketCategory.Type.ORGANIZATION],
            },
            {
                SupportTicketCategory.title.field.name: "AI Interview",
                SupportTicketCategory.types.field.name: [
                    SupportTicketCategory.Type.JOB_SEEKER,
                    SupportTicketCategory.Type.ORGANIZATION,
                ],
            },
            {
                SupportTicketCategory.title.field.name: "Post Hiring",
                SupportTicketCategory.types.field.name: [
                    SupportTicketCategory.Type.JOB_SEEKER,
                    SupportTicketCategory.Type.ORGANIZATION,
                ],
            },
        ]

        SupportTicketCategory.objects.bulk_create(
            [
                SupportTicketCategory(
                    **instance_dict,
                )
                for instance_dict in instance_dicts
            ],
            update_conflicts=True,
            unique_fields=[SupportTicketCategory.title.field.name],
            update_fields=[SupportTicketCategory.types.field.name],
            batch_size=10,
        )
