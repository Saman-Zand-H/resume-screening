from django.db.models import Value, CharField
from django.db.models.functions import Concat
import django_filters

from common.utils import fields_join

from .models import (
    OrganizationEmployee,
    OrganizationEmployeeCooperation,
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
            OrganizationEmployee.organization.field.name: ["exact"],
            fields_join(
                OrganizationEmployee.user,
                JobPositionAssignment.job_seeker.field.related_query_name(),
                JobPositionAssignment.job_position,
            ): ["exact"],
            fields_join(
                OrganizationEmployeeCooperation.employee.field.related_query_name(),
                OrganizationEmployeeCooperation.status,
            ): ["exact"],
        }

    def filter_full_name(self, queryset, name, value):
        first_name = fields_join(OrganizationEmployee.user, User.first_name)
        last_name = fields_join(OrganizationEmployee.user, User.last_name)
        return queryset.annotate(full_name=Concat(first_name, Value(" "), last_name, output_field=CharField())).filter(
            full_name__icontains=value
        )

    def _filter_cooperation_start_at(self, queryset, value, opt="exact"):
        return queryset.filter(
            **{
                fields_join(
                    OrganizationEmployeeCooperation.employee.field.related_query_name(),
                    OrganizationEmployeeCooperation.start_at,
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
