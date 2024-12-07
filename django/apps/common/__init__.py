import json
import warnings

import graphene
from django_filters import BaseCSVFilter, CharFilter
from django_filters.filters import ChoiceFilter
from graphene_django.converter import convert_choice_field_to_enum
from graphene_django.filter.fields import DjangoFilterConnectionField
from graphene_django.filter.filterset import (
    FILTER_FOR_DBFIELD_DEFAULTS,
    GRAPHENE_FILTER_SET_OVERRIDES,
    GrapheneFilterSetMixin,
)

from django.contrib.postgres.fields import ArrayField
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import QuerySet


class CharArrayFilter(BaseCSVFilter, CharFilter):
    pass


def __monkeypatch_graphene_filterset_mixin__():
    filters = {key: FILTER_FOR_DBFIELD_DEFAULTS[key] for key in set(GRAPHENE_FILTER_SET_OVERRIDES.keys())}

    filters.update({ArrayField: {"filter_class": CharArrayFilter}})

    GrapheneFilterSetMixin.FILTER_DEFAULTS.update(filters)


__monkeypatch_graphene_filterset_mixin__()


class DjangoQuerysetEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, QuerySet):
            return list(obj)

        if hasattr(obj, "__dict__"):
            return {key: value for key, value in obj.__dict__.items() if not key.startswith("_")}

        return super().default(obj)


original_dumps = json.dumps


def patched_dumps(obj, *args, **kwargs):
    if "cls" not in kwargs:
        kwargs["cls"] = DjangoQuerysetEncoder
    return original_dumps(obj, *args, **kwargs)


json.dumps = patched_dumps


def custom_showwarning(message, category, filename, lineno, file=None, line=None):
    """Override default warning display, hiding specific warnings."""
    ignored_files = ["google/genai"]
    ignored_messages = [
        "is not a Python type (it may be an instance of an object)",
        "unclosed file",
        "is still running",
    ]

    if any(ignored_file in str(filename) for ignored_file in ignored_files):
        return
    if any(ignored_message in str(message) for ignored_message in ignored_messages):
        return

    original_showwarning(message, category, filename, lineno, file, line)


original_showwarning = warnings.showwarning

warnings.showwarning = custom_showwarning


original_django_filter_connection_field_filtering_args = DjangoFilterConnectionField.filtering_args


@property
def django_filter_connection_field_filtering_args(self):
    filtering_args = original_django_filter_connection_field_filtering_args.fget(self)
    if self._filtering_args:
        model = self.filterset_class._meta.model
        for field_name, filter_field in self.filterset_class.base_filters.items():
            required = filter_field.extra.get("required", False)
            if type(filter_field) is ChoiceFilter and filtering_args[field_name].type == graphene.String:
                filtering_args[field_name] = graphene.Argument(
                    convert_choice_field_to_enum(getattr(model, field_name).field),
                    description=filter_field.label,
                    required=required,
                )
    return filtering_args


DjangoFilterConnectionField.filtering_args = django_filter_connection_field_filtering_args
