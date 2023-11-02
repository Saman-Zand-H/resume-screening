import graphene
from graphene_django.filter import DjangoFilterConnectionField

from .types import CityNode, CountryNode, FieldNode, JobNode, RegionNode, UniversityNode, LanguageNode, LanguageProficiencyTestNode


class CommonQuery(graphene.ObjectType):
    universities = DjangoFilterConnectionField(UniversityNode)
    fields = DjangoFilterConnectionField(FieldNode)
    countries = DjangoFilterConnectionField(CountryNode)
    regions = DjangoFilterConnectionField(RegionNode)
    cities = DjangoFilterConnectionField(CityNode)
    jobs = DjangoFilterConnectionField(JobNode)
    languages = DjangoFilterConnectionField(LanguageNode)
    languages_proficiency_tests = DjangoFilterConnectionField(LanguageProficiencyTestNode)


class Query(graphene.ObjectType):
    common = graphene.Field(CommonQuery)

    def resolve_common(self, info):
        return CommonQuery()
