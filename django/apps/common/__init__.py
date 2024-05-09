from django_filters import BaseCSVFilter, CharFilter
from graphene_django.filter.filterset import (
    FILTER_FOR_DBFIELD_DEFAULTS,
    GRAPHENE_FILTER_SET_OVERRIDES,
    GrapheneFilterSetMixin,
)

from django.contrib.postgres.fields import ArrayField


class CharArrayFilter(BaseCSVFilter, CharFilter):
    pass


def __monkeypatch_graphene_filterset_mixin__():
    filters = {key: FILTER_FOR_DBFIELD_DEFAULTS[key] for key in set(GRAPHENE_FILTER_SET_OVERRIDES.keys())}

    filters.update({ArrayField: {"filter_class": CharArrayFilter}})

    GrapheneFilterSetMixin.FILTER_DEFAULTS.update(filters)


__monkeypatch_graphene_filterset_mixin__()
