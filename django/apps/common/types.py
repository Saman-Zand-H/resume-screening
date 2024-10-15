from operator import itemgetter

import graphene
from cities_light.graphql.types import City as CityTypeBase
from cities_light.graphql.types import Country as CountryTypeBase
from cities_light.graphql.types import Region as RegionTypeBase
from cities_light.graphql.types import SubRegion as SubRegionTypeBase
from cities_light.models import City, Country, Region, SubRegion
from graphene_django.converter import convert_choices_to_named_enum_with_descriptions
from graphene_django_optimizer import OptimizedDjangoObjectType as DjangoObjectType

from .exceptions import Error, Errors
from .mixins import ArrayChoiceTypeMixin
from .models import (
    Field,
    FileModel,
    Industry,
    Job,
    JobBenefit,
    LanguageProficiencySkill,
    LanguageProficiencyTest,
    Skill,
    University,
)
from .utils import get_file_models

enum_values = [(v.code, v.message) for k, v in vars(Errors).items() if isinstance(v, Error)]
ErrorType = graphene.Enum("Errors", enum_values)


class JobBenefitNode(DjangoObjectType):
    class Meta:
        model = JobBenefit
        use_connection = True
        fields = (
            JobBenefit.id.field.name,
            JobBenefit.name.field.name,
        )
        filter_fields = {
            JobBenefit.id.field.name: ["exact"],
            JobBenefit.name.field.name: ["icontains"],
        }


class JobBenefitType(DjangoObjectType):
    class Meta:
        model = JobBenefit
        fields = (
            JobBenefit.id.field.name,
            JobBenefit.name.field.name,
        )


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


class JobNode(DjangoObjectType):
    class Meta:
        model = Job
        use_connection = True
        fields = (
            Job.id.field.name,
            Job.title.field.name,
            Job.industries.field.name,
            Job.require_appearance_data.field.name,
        )
        filter_fields = {
            Job.id.field.name: ["exact"],
            Job.title.field.name: ["icontains"],
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


class FieldType(DjangoObjectType):
    class Meta:
        model = Field
        fields = (
            Field.id.field.name,
            Field.name.field.name,
        )


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


class LanguageProficiencyTestNode(ArrayChoiceTypeMixin, DjangoObjectType):
    class Meta:
        model = LanguageProficiencyTest
        use_connection = True
        fields = (
            LanguageProficiencyTest.id.field.name,
            LanguageProficiencyTest.title.field.name,
            LanguageProficiencyTest.languages.field.name,
            LanguageProficiencySkill.test.field.related_query_name(),
        )
        filter_fields = {
            LanguageProficiencyTest.id.field.name: ["exact"],
            LanguageProficiencyTest.title.field.name: ["icontains"],
            LanguageProficiencyTest.languages.field.name: ["contains"],
        }


class LanguageProficiencySkillNode(DjangoObjectType):
    class Meta:
        model = LanguageProficiencySkill
        use_connection = True
        fields = (
            LanguageProficiencySkill.id.field.name,
            LanguageProficiencySkill.skill_name.field.name,
            LanguageProficiencySkill.slug.field.name,
            LanguageProficiencySkill.validator_kwargs.field.name,
        )


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


class SkillType(DjangoObjectType):
    class Meta:
        model = Skill
        fields = (
            Skill.id.field.name,
            Skill.title.field.name,
        )


UploadType = convert_choices_to_named_enum_with_descriptions(
    "UploadType",
    sorted(((model.SLUG, model._meta.verbose_name) for model in get_file_models()), key=itemgetter(0)),
)


def create_file_model_type(model):
    class Meta:
        model = model
        fields = [FileModel.file.field.name]

    class_name = f"{model.__name__}Type"
    return type(class_name, (DjangoObjectType,), {"Meta": Meta})


for model in get_file_models():
    globals()[f"{model.__name__}Type"] = create_file_model_type(model)
