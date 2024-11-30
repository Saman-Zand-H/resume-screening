from typing import List, NamedTuple

from cities_light.models import City, Country
from common.populators import BasePopulator
from common.utils import fj
from flex_report.models import Column

from django.contrib.contenttypes.models import ContentType
from django.db.models import Model

from .accesses import AccessContainer, AccessType
from .choices import DefaultRoles
from .models import Access, Profile, Role, SupportTicketCategory, User


class ColumnInitialData(NamedTuple):
    model: Model
    columns: List[str]


class ColumnPopulator(BasePopulator):
    def populate(self):
        initial_data = [
            ColumnInitialData(
                model=Profile,
                columns=[
                    fj(Profile.user, User.first_name),
                    fj(Profile.user, User.last_name),
                    fj(Profile.user, User.email),
                    Profile.gender.field.name,
                    Profile.avatar.field.name,
                    Profile.employment_status.field.name,
                    Profile.interested_jobs.field.name,
                    Profile.skills.field.name,
                    Profile.raw_skills.field.name,
                    Profile.city.field.name,
                    fj(Profile.city, City.country, Country.name),
                    Profile.native_language.field.name,
                    Profile.fluent_languages.field.name,
                    Profile.score.field.name,
                    Profile.credits.field.name,
                    Profile.birth_date.field.name,
                    Profile.accept_terms_and_conditions.field.name,
                    Profile.allow_notifications.field.name,
                ],
            )
        ]
        for data in initial_data:
            content_type = ContentType.objects.get_for_model(data.model)
            Column.objects.bulk_create(
                [
                    Column(
                        **{
                            Column.model.field.name: content_type,
                            Column.title.field.name: column_title,
                        }
                    )
                    for column_title in data.columns
                ],
                batch_size=10,
                ignore_conflicts=True,
            )


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
