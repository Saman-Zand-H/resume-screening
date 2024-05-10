import graphene
from graphene_django.filter import DjangoFilterConnectionField

from .types import CVTemplateNode


class CVQuery(graphene.ObjectType):
    templates = DjangoFilterConnectionField(CVTemplateNode)


class Query(graphene.ObjectType):
    cv = graphene.Field(CVQuery)

    def resolve_cv(self, info):
        return CVQuery()
