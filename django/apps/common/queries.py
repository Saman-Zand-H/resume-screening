import graphene
from graphene_django.filter import DjangoFilterConnectionField

from .models import Field, University
from .types import CityNode, FieldType, UniversityType


class CommonQuery(graphene.ObjectType):
    universities = graphene.List(UniversityType)
    fields = graphene.List(FieldType)
    cities = DjangoFilterConnectionField(CityNode, max_limit=15)

    def resolve_universities(self, info):
        return University.objects.all()

    def resolve_fields(self, info):
        return Field.objects.all()


class Query(graphene.ObjectType):
    common = graphene.Field(CommonQuery)

    def resolve_common(self, info):
        return CommonQuery()
