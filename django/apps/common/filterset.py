import django_filters
from flex_report.filterset import (
    FILTERSET_DATE_FILTERS,
    CustomModelMultipleChoiceFilter,
)
from flex_report.filterset import FilterSet as BaseFilterSet

from django.contrib.admin.options import FORMFIELD_FOR_DBFIELD_DEFAULTS


class FilterSet(BaseFilterSet):
    @classmethod
    def get_form_field_widget(cls, f):
        field_defaults = FORMFIELD_FOR_DBFIELD_DEFAULTS.get(f.__class__, {})
        return field_defaults.get("widget")

    @classmethod
    def get_form_field_class(cls, f):
        field_defaults = FORMFIELD_FOR_DBFIELD_DEFAULTS.get(f.__class__, {})
        return field_defaults.get("field_class")

    @classmethod
    def filter_for_lookup(cls, f, lookup_type):
        filter_, opts = super().filter_for_lookup(f, lookup_type)
        modified_widget = cls.get_form_field_widget(f)
        modified_field_class = cls.get_form_field_class(f)
        widget = lambda w, attrs=None: w(attrs=attrs) if attrs else w()  # noqa

        if isinstance(filter_, django_filters.ModelMultipleChoiceFilter) and "choices" in opts:
            filter_ = django_filters.MultipleChoiceFilter
            opts["widget"] = widget(modified_widget or filter_.field_class.widget)

        elif isinstance(filter_, django_filters.ModelChoiceFilter):
            filter_ = django_filters.ModelMultipleChoiceFilter
            opts["widget"] = widget(modified_widget or filter_.field_class.widget)

        elif issubclass(filter_, tuple(FILTERSET_DATE_FILTERS)):
            opts["widget"] = widget(modified_widget or filter_.field_class.widget)
            filter_.field_class = modified_field_class or filter_.field_class

        elif issubclass(filter_, django_filters.BaseInFilter):
            filter_ = CustomModelMultipleChoiceFilter
            opts["widget"] = widget(modified_widget or filter_.field_class.widget)

        return filter_, opts
