from graphene_django.filter.filterset import (
    FILTER_FOR_DBFIELD_DEFAULTS,
    GRAPHENE_FILTER_SET_OVERRIDES,
    GrapheneFilterSetMixin,
)


def __monkeypatch_graphene_filterset_mixin__():
    GrapheneFilterSetMixin.FILTER_DEFAULTS.update(
        {key: FILTER_FOR_DBFIELD_DEFAULTS[key] for key in set(GRAPHENE_FILTER_SET_OVERRIDES.keys())}
    )


__monkeypatch_graphene_filterset_mixin__()
