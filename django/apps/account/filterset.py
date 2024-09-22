from django.db.models import Value, CharField
from django.db.models.functions import Concat
import django_filters

from common.utils import fields_join

from .models import (
    OrganizationJobPosition,
    OrganizationEmployee,
    OrganizationEmployeeCooperationHistory,
    JobPositionAssignment,
    User,
)


class OrganizationEmployeeFilterset(django_filters.FilterSet):
    full_name = django_filters.CharFilter(method="filter_full_name")
    cooperation_start_at = django_filters.DateFilter(method="filter_cooperation_start_at")
    cooperation_start_at_gte = django_filters.DateFilter(method="filter_cooperation_start_at_gte")
    cooperation_start_at_lte = django_filters.DateFilter(method="filter_cooperation_start_at_lte")

    class Meta:
        model = OrganizationEmployee
        fields = {
            fields_join(
                OrganizationEmployee.job_position_assignment,
                JobPositionAssignment.job_position,
                OrganizationJobPosition.organization,
            ): ["exact"],
            fields_join(
                OrganizationEmployee.job_position_assignment,
                JobPositionAssignment.job_position,
            ): ["exact"],
            OrganizationEmployee.hiring_status.field.name: ["exact"],
        }

    def filter_full_name(self, queryset, name, value):
        job_seeker = fields_join(OrganizationEmployee.job_position_assignment, JobPositionAssignment.job_seeker)
        first_name = fields_join(job_seeker, User.first_name)
        last_name = fields_join(job_seeker, User.last_name)
        return queryset.annotate(full_name=Concat(first_name, Value(" "), last_name, output_field=CharField())).filter(
            full_name__icontains=value
        )

    def _filter_cooperation_start_at(self, queryset, value, opt="exact"):
        return queryset.filter(
            **{
                fields_join(
                    OrganizationEmployeeCooperationHistory.employee.field.related_query_name(),
                    OrganizationEmployeeCooperationHistory.start_at,
                    opt,
                ): value
            }
        ).distinct()

    def filter_cooperation_start_at(self, queryset, name, value):
        return self._filter_cooperation_start_at(queryset, value)

    def filter_cooperation_start_at_gte(self, queryset, name, value):
        return self._filter_cooperation_start_at(queryset, value, "gte")

    def filter_cooperation_start_at_lte(self, queryset, name, value):
        return self._filter_cooperation_start_at(queryset, value, "lte")
