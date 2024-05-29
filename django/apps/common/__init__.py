import json

from django_filters import BaseCSVFilter, CharFilter
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
