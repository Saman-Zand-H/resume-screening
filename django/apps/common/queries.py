import graphene
from graphene_django.filter import DjangoFilterConnectionField

from .types import (
    ErrorType,
    CityNode,
    CountryNode,
    FieldNode,
    RegionNode,
    UniversityNode,
    LanguageType,
    LanguageProficiencyTestNode,
    JobIndustryNode,
    JobCategoryNode,
    SkillNode,
    PositionNode,
    JobNode,
)

from common.choices import LANGUAGES


class CommonQuery(graphene.ObjectType):
    languages = graphene.List(LanguageType, name=graphene.String())
    universities = DjangoFilterConnectionField(UniversityNode)
    fields = DjangoFilterConnectionField(FieldNode)
    countries = DjangoFilterConnectionField(CountryNode)
    regions = DjangoFilterConnectionField(RegionNode)
    cities = DjangoFilterConnectionField(CityNode)
    languages_proficiency_tests = DjangoFilterConnectionField(LanguageProficiencyTestNode)
    job_industries = DjangoFilterConnectionField(JobIndustryNode)
    job_categories = DjangoFilterConnectionField(JobCategoryNode)
    skills = DjangoFilterConnectionField(SkillNode)
    positions = DjangoFilterConnectionField(PositionNode)
    jobs = DjangoFilterConnectionField(JobNode)

    def resolve_languages(self, info, name=None):
        filtered_languages = LANGUAGES
        if name:
            filtered_languages = [lang for lang in filtered_languages if name.lower() in lang[1].lower()]
        return [LanguageType(code=lang[0], name=lang[1]) for lang in filtered_languages]


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
