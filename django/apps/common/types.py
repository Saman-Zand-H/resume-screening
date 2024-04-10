import graphene
from cities_light.graphql.types import City as CityTypeBase
from cities_light.graphql.types import Country as CountryTypeBase
from cities_light.graphql.types import Region as RegionTypeBase
from cities_light.graphql.types import SubRegion as SubRegionTypeBase
from cities_light.models import City, Country, Region, SubRegion
from graphene_django_optimizer import OptimizedDjangoObjectType as DjangoObjectType

from .exceptions import Error, Errors
from .models import (
    Field,
    Industry,
    Job,
    JobCategory,
    LanguageProficiencyTest,
    Position,
    Skill,
    University,
)

enum_values = [(v.code, v.message) for k, v in vars(Errors).items() if isinstance(v, Error)]
ErrorType = graphene.Enum("Errors", enum_values)


class IndustryNode(DjangoObjectType):
    class Meta:
        model = Industry
        use_connection = True
        fields = (
            Industry.id.field.name,
            Industry.title.field.name,
        )
        filter_fields = {
            Industry.id.field.name: ["exact"],
            Industry.title.field.name: ["icontains"],
        }


class JobCategoryNode(DjangoObjectType):
    class Meta:
        model = JobCategory
        use_connection = True
        fields = (
            JobCategory.id.field.name,
            JobCategory.title.field.name,
        )
        filter_fields = {
            JobCategory.id.field.name: ["exact"],
            JobCategory.title.field.name: ["icontains"],
        }


class JobNode(DjangoObjectType):
    class Meta:
        model = Job
        use_connection = True
        fields = (
            Job.id.field.name,
            Job.title.field.name,
            Job.category.field.name,
            Job.require_appearance_data.field.name,
        )
        filter_fields = {
            Job.id.field.name: ["exact"],
            Job.title.field.name: ["icontains"],
            Job.category.field.name: ["exact"],
        }


class UniversityNode(DjangoObjectType):
    class Meta:
        model = University
        use_connection = True
        fields = (
            University.id.field.name,
            University.name.field.name,
            University.websites.field.name,
        )
        filter_fields = {
            University.id.field.name: ["exact"],
            University.name.field.name: ["icontains"],
        }


class FieldNode(DjangoObjectType):
    class Meta:
        model = Field
        use_connection = True
        fields = (
            Field.id.field.name,
            Field.name.field.name,
        )
        filter_fields = {
            Field.id.field.name: ["exact"],
            Field.name.field.name: ["icontains"],
        }


class CountryNode(DjangoObjectType):
    class Meta:
        model = Country
        use_connection = True
        fields = [Country.id.field.name] + list(CountryTypeBase._meta.fields.keys())
        filter_fields = {
            Country.id.field.name: ["exact"],
            Country.name.field.name: ["icontains"],
        }


class RegionNode(DjangoObjectType):
    class Meta:
        model = Region
        use_connection = True
        fields = [Region.id.field.name] + list(RegionTypeBase._meta.fields.keys())
        filter_fields = {
            Region.id.field.name: ["exact"],
            Region.name.field.name: ["icontains"],
            Region.country.field.name: ["exact"],
        }


class SubRegionNode(DjangoObjectType):
    class Meta:
        model = SubRegion
        use_connection = True
        fields = [SubRegion.id.field.name] + list(SubRegionTypeBase._meta.fields.keys())


class CityNode(DjangoObjectType):
    class Meta:
        model = City
        use_connection = True
        fields = [City.id.field.name] + list(CityTypeBase._meta.fields.keys())
        filter_fields = {
            City.id.field.name: ["exact"],
            City.name.field.name: ["icontains"],
            City.region.field.name: ["exact"],
            "country__code2": ["exact"],
        }


class LanguageType(graphene.ObjectType):
    code = graphene.String()
    name = graphene.String()


class LanguageProficiencyTestNode(DjangoObjectType):
    class Meta:
        model = LanguageProficiencyTest
        use_connection = True
        fields = (
            LanguageProficiencyTest.id.field.name,
            LanguageProficiencyTest.title.field.name,
            LanguageProficiencyTest.min_score.field.name,
            LanguageProficiencyTest.max_score.field.name,
        )
        filter_fields = {
            LanguageProficiencyTest.id.field.name: ["exact"],
            LanguageProficiencyTest.title.field.name: ["icontains"],
        }


class PositionNode(DjangoObjectType):
    class Meta:
        model = Position
        use_connection = True
        fields = (
            Position.id.field.name,
            Position.title.field.name,
        )
        filter_fields = {
            Position.id.field.name: ["exact"],
            Position.title.field.name: ["icontains"],
        }


class SkillNode(DjangoObjectType):
    class Meta:
        model = Skill
        use_connection = True
        fields = (
            Skill.id.field.name,
            Skill.title.field.name,
        )
        filter_fields = {
            Skill.id.field.name: ["exact"],
            Skill.title.field.name: ["icontains"],
        }

    @classmethod
    def get_queryset(cls, queryset, info):
        return queryset.system()
