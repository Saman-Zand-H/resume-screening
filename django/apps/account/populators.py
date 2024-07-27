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
                SupportTicketCategory.slug.field.name: "profile",
                SupportTicketCategory.title.field.name: "Profile",
                SupportTicketCategory.is_organization.field.name: False,
                SupportTicketCategory.is_job_seeker.field.name: True,
            },
            {
                SupportTicketCategory.slug.field.name: "resume",
                SupportTicketCategory.title.field.name: "Resume",
                SupportTicketCategory.is_organization.field.name: False,
                SupportTicketCategory.is_job_seeker.field.name: True,
            },
            {
                SupportTicketCategory.slug.field.name: "job_interest",
                SupportTicketCategory.title.field.name: "Job Interest",
                SupportTicketCategory.is_organization.field.name: False,
                SupportTicketCategory.is_job_seeker.field.name: True,
            },
            {
                SupportTicketCategory.slug.field.name: "academy",
                SupportTicketCategory.title.field.name: "Academy",
                SupportTicketCategory.is_organization.field.name: False,
                SupportTicketCategory.is_job_seeker.field.name: True,
            },
            {
                SupportTicketCategory.slug.field.name: "assessment",
                SupportTicketCategory.title.field.name: "Assessment",
                SupportTicketCategory.is_organization.field.name: False,
                SupportTicketCategory.is_job_seeker.field.name: True,
            },
            {
                SupportTicketCategory.slug.field.name: "job_suggestion",
                SupportTicketCategory.title.field.name: "Job Suggestion",
                SupportTicketCategory.is_organization.field.name: False,
                SupportTicketCategory.is_job_seeker.field.name: True,
            },
            {
                SupportTicketCategory.slug.field.name: "ai_interview",
                SupportTicketCategory.title.field.name: "AI Interview",
                SupportTicketCategory.is_organization.field.name: False,
                SupportTicketCategory.is_job_seeker.field.name: True,
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
            update_fields=[
                SupportTicketCategory.title.field.name,
                SupportTicketCategory.is_job_seeker.field.name,
                SupportTicketCategory.is_organization.field.name,
            ],
            unique_fields=[SupportTicketCategory.slug.field.name],
            batch_size=10,
        )
