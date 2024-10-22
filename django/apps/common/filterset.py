import django_filters
from flex_report.constants import FILTERSET_DATE_FILTERS
from flex_report.filterset import (
    CustomModelMultipleChoiceFilter,
)
from flex_report.filterset import FilterSet as BaseFilterSet

from django.contrib.admin.options import FORMFIELD_FOR_DBFIELD_DEFAULTS
from django.contrib.postgres.fields import ArrayField
from django.db.models.constants import LOOKUP_SEP


class OverlapsFilter(django_filters.MultipleChoiceFilter):
    def get_filter_predicate(self, v):
        name = self.field_name
        if name:
            name = LOOKUP_SEP.join([name, self.lookup_expr])
        predicate = super().get_filter_predicate(v)
        predicate[name] = [v]
        return predicate


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
        filter_, opts = super(BaseFilterSet, cls).filter_for_lookup(f, lookup_type)
        modified_widget = cls.get_form_field_widget(f)
        modified_field_class = cls.get_form_field_class(f)
        widget = lambda w, attrs=None: w(attrs=attrs) if attrs else w()  # noqa

        if isinstance(filter_, django_filters.ModelMultipleChoiceFilter) and "choices" in opts:
            filter_ = django_filters.MultipleChoiceFilter
            opts["widget"] = widget(modified_widget or filter_.field_class.widget)

        elif isinstance(f, ArrayField):
            filter_ = OverlapsFilter
            opts["widget"] = widget(modified_widget or filter_.field_class.widget)
            opts["choices"] = getattr(f, "choices", [])

        elif isinstance(filter_, django_filters.ModelChoiceFilter):
            filter_ = django_filters.ModelMultipleChoiceFilter
            opts["widget"] = widget(modified_widget or filter_.field_class.widget)

        elif issubclass(filter_, tuple(FILTERSET_DATE_FILTERS)):
            opts["widget"] = widget(modified_widget or filter_.field_class.widget)
            filter_.field_class = modified_field_class or filter_.field_class

        elif issubclass(filter_, django_filters.BaseInFilter):
            filter_ = CustomModelMultipleChoiceFilter
            opts["widget"] = widget(modified_widget or filter_.field_class.widget)

        else:
            filter_, opts = super().filter_for_lookup(f, lookup_type)

        return filter_, opts
