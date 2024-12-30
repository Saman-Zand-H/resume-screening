from operator import itemgetter

import graphene
from account.models import Education, WorkExperience
from cities_light.graphql.types import City as CityTypeBase
from cities_light.graphql.types import Country as CountryTypeBase
from cities_light.graphql.types import Region as RegionTypeBase
from cities_light.graphql.types import SubRegion as SubRegionTypeBase
from cities_light.models import City, Country, Region, SubRegion
from flex_blob.models import FileModel as BaseFileModel
from graphene_django.converter import convert_choices_to_named_enum_with_descriptions
from graphene_django_optimizer import OptimizedDjangoObjectType as DjangoObjectType

from common.utils import fj
from django.db.models.lookups import Contains, Exact, IContains

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
from .utils import get_file_models, get_verification_method_file_models

enum_values = [(v.code, v.message) for v in vars(Errors).values() if isinstance(v, Error)]
ErrorType = graphene.Enum("Errors", enum_values)


class NullableFieldsDjangoObjectType(DjangoObjectType):
    @classmethod
    def __init_subclass_with_meta__(cls, *args, **kwargs):
        super().__init_subclass_with_meta__(*args, **kwargs)
        for field_name, field in cls._meta.fields.items():
            if isinstance(field.type, graphene.NonNull):
                cls._meta.fields[field_name] = graphene.Field(
                    field.type.of_type,
                    *field.type.args,
                    **field.type.kwargs,
                )

    class Meta:
        abstract = True


class JobBenefitNode(DjangoObjectType):
    class Meta:
        model = JobBenefit
        use_connection = True
        fields = (
            JobBenefit.id.field.name,
            JobBenefit.name.field.name,
        )
        filter_fields = {
            JobBenefit.id.field.name: [Exact.lookup_name],
            JobBenefit.name.field.name: [IContains.lookup_name],
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
            Industry.id.field.name: [Exact.lookup_name],
            Industry.title.field.name: [IContains.lookup_name],
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
            Job.id.field.name: [Exact.lookup_name],
            Job.title.field.name: [IContains.lookup_name],
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
            University.id.field.name: [Exact.lookup_name],
            University.name.field.name: [IContains.lookup_name],
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
            Field.id.field.name: [Exact.lookup_name],
            Field.name.field.name: [IContains.lookup_name],
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
            Country.id.field.name: [Exact.lookup_name],
            Country.name.field.name: [IContains.lookup_name],
        }


class RegionNode(DjangoObjectType):
    class Meta:
        model = Region
        use_connection = True
        fields = [Region.id.field.name] + list(RegionTypeBase._meta.fields.keys())
        filter_fields = {
            Region.id.field.name: [Exact.lookup_name],
            Region.name.field.name: [IContains.lookup_name],
            Region.country.field.name: [Exact.lookup_name],
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
            City.id.field.name: [Exact.lookup_name],
            City.name.field.name: [IContains.lookup_name],
            City.region.field.name: [Exact.lookup_name],
            fj(City.country, Country.code2): [Exact.lookup_name],
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
            LanguageProficiencyTest.id.field.name: [Exact.lookup_name],
            LanguageProficiencyTest.title.field.name: [IContains.lookup_name],
            LanguageProficiencyTest.languages.field.name: [Contains.lookup_name],
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
            Skill.id.field.name: [Exact.lookup_name],
            Skill.title.field.name: [IContains.lookup_name],
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


WorkExperienceVerificationMethodUploadType = convert_choices_to_named_enum_with_descriptions(
    "WorkExperienceVerificationMethodUploadType",
    sorted(
        ((model.SLUG, model._meta.verbose_name) for model in get_verification_method_file_models(WorkExperience)),
        key=itemgetter(0),
    ),
)

EducationVerificationMethodUploadType = convert_choices_to_named_enum_with_descriptions(
    "EducationVerificationMethodUploadType",
    sorted(
        ((model.SLUG, model._meta.verbose_name) for model in get_verification_method_file_models(Education)),
        key=itemgetter(0),
    ),
)


class BaseFileModelType(DjangoObjectType):
    class Meta:
        model = BaseFileModel
        fields = [BaseFileModel.id.field.name, BaseFileModel.file.field.name]


def create_file_model_type(model):
    class Meta:
        model = model
        fields = [FileModel.file.field.name]

    class_name = f"{model.__name__}Type"
    return type(class_name, (DjangoObjectType,), {"Meta": Meta})


for model in get_file_models():
    globals()[f"{model.__name__}Type"] = create_file_model_type(model)
