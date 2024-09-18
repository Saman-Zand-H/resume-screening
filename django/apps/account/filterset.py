from django.db.models import Value, CharField
from django.db.models.functions import Concat
import django_filters

from common.utils import fields_join

from .models import OrganizationJobPosition, OrganizationEmployee, JobPositionAssignment, User


class OrganizationEmployeeFilterset(django_filters.FilterSet):
    full_name = django_filters.CharFilter(method="filter_full_name")

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
            OrganizationEmployee.cooperation_start_at.field.name: ["exact", "lt", "gt"],
        }

    def filter_full_name(self, queryset, name, value):
        job_seeker = fields_join(OrganizationEmployee.job_position_assignment, JobPositionAssignment.job_seeker)
        first_name = fields_join(job_seeker, User.first_name)
        last_name = fields_join(job_seeker, User.last_name)
        return queryset.annotate(full_name=Concat(first_name, Value(" "), last_name, output_field=CharField())).filter(
            full_name__icontains=value
        )
