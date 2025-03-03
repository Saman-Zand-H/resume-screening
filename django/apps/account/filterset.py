import django_filters
from common.utils import fj

from django.db.models import CharField, QuerySet, Value
from django.db.models.functions import Concat
from django.db.models.lookups import (
    Exact,
    GreaterThanOrEqual,
    IContains,
    LessThanOrEqual,
    In,
)
from django.utils.translation import gettext_lazy as _

from .constants import OrganizationEmployeeAnnotationNames
from .models import (
    JobPositionAssignment,
    OrganizationEmployee,
    OrganizationEmployeeCooperation,
    User,
)


class OrganizationEmployeeFilterset(django_filters.FilterSet):
    def filter_full_name(self, queryset: QuerySet[OrganizationEmployee], name, value: str):
        first_name = fj(OrganizationEmployee.user, User.first_name)
        last_name = fj(OrganizationEmployee.user, User.last_name)
        full_name_concat = Concat(
            first_name,
            Value(" "),
            last_name,
            output_field=CharField(verbose_name=_("Full Name")),
        )

        return queryset.annotate(**{OrganizationEmployeeAnnotationNames.USER_FULL_NAME: full_name_concat}).filter(
            **{fj(OrganizationEmployeeAnnotationNames.USER_FULL_NAME, IContains.lookup_name): value}
        )

    def _filter_cooperation_start_at(self, queryset, value, opt=Exact.lookup_name):
        return queryset.filter(
            **{
                fj(
                    OrganizationEmployeeCooperation.employee.field.related_query_name(),
                    OrganizationEmployeeCooperation.start_at,
                    opt,
                ): value
            }
        ).distinct()

    def filter_cooperation_start_at(self, queryset, name, value):
        return self._filter_cooperation_start_at(queryset, value)

    def filter_cooperation_start_at_gte(self, queryset, name, value):
        return self._filter_cooperation_start_at(queryset, value, GreaterThanOrEqual.lookup_name)

    def filter_cooperation_start_at_lte(self, queryset, name, value):
        return self._filter_cooperation_start_at(queryset, value, LessThanOrEqual.lookup_name)

    full_name = django_filters.CharFilter(method=filter_full_name.__name__)
    cooperation_start_at = django_filters.DateFilter(method=filter_cooperation_start_at.__name__)
    cooperation_start_at_gte = django_filters.DateFilter(method=filter_cooperation_start_at_gte.__name__)
    cooperation_start_at_lte = django_filters.DateFilter(method=filter_cooperation_start_at_lte.__name__)

    class Meta:
        model = OrganizationEmployee
        fields = {
            OrganizationEmployee.organization.field.name: [Exact.lookup_name],
            fj(
                OrganizationEmployee.user,
                JobPositionAssignment.job_seeker.field.related_query_name(),
                JobPositionAssignment.job_position,
            ): [Exact.lookup_name],
            fj(
                OrganizationEmployeeCooperation.employee.field.related_query_name(),
                OrganizationEmployeeCooperation.status,
            ): [Exact.lookup_name],
        }


class JobPositionAssignmentFilterset(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(
        method="filter_status",
        choices=JobPositionAssignment.JobSeekerStatus.choices,
    )

    def filter_status(self, queryset, name, value):
        return queryset.filter(
            **{
                fj(JobPositionAssignment.status, In.lookup_name): JobPositionAssignment.map_job_seeker_status_to_status(
                    value
                )
            }
    )

    class Meta:
        model = JobPositionAssignment
        fields = [
            JobPositionAssignment._meta.pk.attname,
        ]
