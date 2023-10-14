import graphene
from graphene_django.filter import DjangoFilterConnectionField

from .types import CityNode, CountryNode, FieldNode, RegionNode, UniversityNode


class CommonQuery(graphene.ObjectType):
    universities = DjangoFilterConnectionField(UniversityNode)
    fields = DjangoFilterConnectionField(FieldNode)
    countries = DjangoFilterConnectionField(CountryNode)
    regions = DjangoFilterConnectionField(RegionNode)
    cities = DjangoFilterConnectionField(CityNode)


class Query(graphene.ObjectType):
    common = graphene.Field(CommonQuery)

    def resolve_common(self, info):
        return CommonQuery()
