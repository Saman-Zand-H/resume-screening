from typing import List, NamedTuple

from common.populators import BasePopulator

from .accesses import AccessContainer, AccessType
from .choices import DefaultRoles
from .models import Access, Role


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
                    Access(slug=access.slug, description=access.description)
                    for access in AccessContainer.get_all_accesses()
                ],
            )
        ]

        Access.objects.bulk_create(
            [
                Access(
                    slug=access.slug,
                    description=access.description,
                )
                for role in access_roles
                for access in role.accesses
            ],
            update_conflicts=True,
            update_fields=[Access.description.field.name],
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
