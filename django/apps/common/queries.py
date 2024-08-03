import graphene
from graphene_django.filter import DjangoFilterConnectionField

from .types import (
    CityNode,
    CountryNode,
    ErrorType,
    FieldNode,
    IndustryNode,
    JobBenefitNode,
    JobCategoryNode,
    JobNode,
    LanguageProficiencyTestNode,
    RegionNode,
    SkillNode,
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
    job_benefits = DjangoFilterConnectionField(JobBenefitNode)
    skills = DjangoFilterConnectionField(SkillNode)


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
