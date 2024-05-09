import graphene
from graphene_django.filter import DjangoFilterConnectionField

from .types import CourseNode


class AcademyQuery(graphene.ObjectType):
    courses = DjangoFilterConnectionField(CourseNode)


class Query(graphene.ObjectType):
    academy = graphene.Field(AcademyQuery)

    def resolve_academy(self, info):
        return AcademyQuery()
