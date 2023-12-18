import graphene
from graphene_django.filter import DjangoFilterConnectionField

from .types import (
    ErrorType,
    CityNode,
    CountryNode,
    FieldNode,
    JobNode,
    RegionNode,
    UniversityNode,
    LanguageNode,
    LanguageProficiencyTestNode,
    JobIndustryNode,
    JobCategoryNode,
    SkillNode,
    PositionNode,
)


class CommonQuery(graphene.ObjectType):
    universities = DjangoFilterConnectionField(UniversityNode)
    fields = DjangoFilterConnectionField(FieldNode)
    countries = DjangoFilterConnectionField(CountryNode)
    regions = DjangoFilterConnectionField(RegionNode)
    cities = DjangoFilterConnectionField(CityNode)
    jobs = DjangoFilterConnectionField(JobNode)
    languages = DjangoFilterConnectionField(LanguageNode)
    languages_proficiency_tests = DjangoFilterConnectionField(LanguageProficiencyTestNode)
    job_industries = DjangoFilterConnectionField(JobIndustryNode)
    job_categories = DjangoFilterConnectionField(JobCategoryNode)
    skills = DjangoFilterConnectionField(SkillNode)
    positions = DjangoFilterConnectionField(PositionNode)


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
