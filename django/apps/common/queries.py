import graphene
from graphene_django.filter import DjangoFilterConnectionField

from common.choices import LANGUAGES

from .types import (
    CityNode,
    CountryNode,
    ErrorType,
    FieldNode,
    IndustryNode,
    JobCategoryNode,
    JobNode,
    LanguageProficiencyTestNode,
    RegionNode,
    UniversityNode,
)


class CommonQuery(graphene.ObjectType):
    universities = DjangoFilterConnectionField(UniversityNode)
    fields = DjangoFilterConnectionField(FieldNode)
    countries = DjangoFilterConnectionField(CountryNode)
    regions = DjangoFilterConnectionField(RegionNode)
    cities = DjangoFilterConnectionField(CityNode)
    languages_proficiency_tests = DjangoFilterConnectionField(LanguageProficiencyTestNode)
    job_categories = DjangoFilterConnectionField(JobCategoryNode)
    jobs = DjangoFilterConnectionField(JobNode)
    industries = DjangoFilterConnectionField(IndustryNode)


class MetaDataQuery(graphene.ObjectType):
    errors = graphene.List(ErrorType)

    def resolve_errors(self, info):
        return list(ErrorType)


class Query(graphene.ObjectType):
    common = graphene.Field(CommonQuery)
    meta_data = graphene.Field(MetaDataQuery)

    def resolve_common(self, info):
        return CommonQuery()

    def resolve_meta_data(self, info):
        return MetaDataQuery()
